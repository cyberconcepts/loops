#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
View class for resource objects.
"""

import urllib
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.interfaces import INameChooser
from zope.app.form.browser.textwidgets import FileWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.formlib.form import FormFields
from zope.formlib.interfaces import DISPLAY_UNWRITEABLE
from zope.proxy import removeAllProxies
from zope.schema.interfaces import IBytes
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName, getParent
from zope.traversing.browser import absoluteURL

from cybertools.browser.action import actions
from cybertools.meta.interfaces import IOptions
from cybertools.typology.interfaces import IType
from cybertools.xedit.browser import ExternalEditorView, fromUnicode
from loops.browser.action import DialogAction, TargetAction
from loops.browser.common import EditForm, BaseView
from loops.browser.concept import BaseRelationView, ConceptRelationView
from loops.browser.concept import ConceptConfigureView
from loops.browser.node import NodeView, node_macros
from loops.common import adapted, NameChooser
from loops.interfaces import IBaseResource, IDocument, ITextDocument
from loops.interfaces import IMediaAsset as legacy_IMediaAsset
from loops.interfaces import ITypeConcept
from loops.media.interfaces import IMediaAsset
from loops.organize.stateful.browser import statefulActions
from loops.organize.util import getRolesForPrincipal
from loops.versioning.browser import version_macros
from loops.versioning.interfaces import IVersionable
from loops import util
from loops.util import _
from loops.wiki.base import wikiLinksActive
from loops.wiki.base import LoopsWikiManager, LoopsWiki, LoopsWikiPage


resource_macros = ViewPageTemplateFile('resource_macros.pt')


class CustomFileWidget(FileWidget):

    def hasInput(self):
        if not self.request.form.get(self.name):
            return False
        return True


class ResourceEditForm(EditForm):

    @property
    def typeInterface(self):
        return IType(self.context).typeInterface

    @property
    def form_fields(self):
        fields = FormFields(IBaseResource)
        typeInterface = self.typeInterface
        if typeInterface is not None:
            omit = [f for f in typeInterface if f in IBaseResource]
            fields = FormFields(fields.omit(*omit), typeInterface)
        dataField = fields['data']
        if IBytes.providedBy(dataField.field):
            dataField.custom_widget = CustomFileWidget
        return fields

    def setUpWidgets(self, ignore_request=False):
        super(ResourceEditForm, self).setUpWidgets(ignore_request)
        desc = self.widgets.get('description')
        if desc:
            desc.height = 2


class DocumentEditForm(EditForm):
    form_fields = FormFields(IDocument)
    for f in form_fields:
        f.render_context |= DISPLAY_UNWRITEABLE


class MediaAssetEditForm(EditForm):
    form_fields = FormFields(legacy_IMediaAsset)


class ResourceView(BaseView):

    template = resource_macros

    @Lazy
    def icon(self):
        if (IMediaAsset.providedBy(self.adapted) and
            'image/' in self.context.contentType):
            self.registerDojoLightbox()
            return dict(src='%s/mediaasset.html?v=minithumb' %
                        (self.nodeView.getUrlForTarget(self.context)))

    @Lazy
    def fullImage(self):
        if (IMediaAsset.providedBy(self.adapted) and
            'image/' in self.context.contentType):
            return dict(src='%s/mediaasset.html?v=medium' %
                                self.nodeView.getUrlForTarget(self.context),
                        title=self.context.title)

    @property
    def macro(self):
        if 'image/' in self.context.contentType:
            return self.template.macros['image']
        else:
            return self.template.macros['download']

    def setupController(self):
        cont = self.controller
        if cont is None:
            return
        if (self.globalOptions('showParentsForAnonymous') or
            not IUnauthenticatedPrincipal.providedBy(self.request.principal)):
            if list(self.relatedConcepts()):
                cont.macros.register('portlet_right', 'related',
                            title=_(u'Related Items'),
                            subMacro=self.template.macros['related'],
                            priority=20, info=self)
            versionable = IVersionable(self.context, None)
            if versionable is not None and len(versionable.versions) > 1:
                    cont.macros.register('portlet_right', 'versions',
                            #title=' '. join((_('Version'), versionable.versionId)),
                            title=_(u'Version ${versionId}',
                                    mapping=dict(versionId=versionable.versionId)),
                            subMacro=version_macros.macros['portlet_versions'],
                            priority=25, info=self)

    def breadcrumbs(self):
        data = []
        if self.breadcrumbsParent is not None:
            data.extend(self.breadcrumbsParent.breadcrumbs())
        if self.context != self.nodeView.targetObject:
            data.append(dict(label=self.title,
                             url=self.nodeView.getUrlForTarget(self.context)))
        return data

    @Lazy
    def breadcrumbsParent(self):
        for c in self.context.getConcepts([self.defaultPredicate]):
            return self.nodeView.getViewForTarget(c, setup=False)

    @Lazy
    def view(self):
        context = self.context
        tp = IType(context).typeProvider
        if tp:
           viewName = ITypeConcept(tp).viewName
           if viewName:
               return component.queryMultiAdapter((context, self.request),
                           name=viewName)
        ct = context.contentType
        ti = IType(context).typeInterface
        if (not ti or issubclass(ti, ITextDocument)
            or (ct.startswith('text/') and ct != 'text/rtf')):
            return DocumentView(context, self.request)
        return self

    def show(self, useAttachment=False):
        """ show means: "download"..."""
        # TODO: control access, e.g. to protected images
        # if self.adapted.isProtected():
        #     raise Unauthorized()
        context = self.context
        ct = context.contentType
        response = self.request.response
        self.recordAccess('show', target=self.uniqueId)
        if ct.startswith('image/'):
            #response.setHeader('Cache-Control', 'public,max-age=86400')
            response.setHeader('Cache-Control', 'max-age=86400')
            adobj = adapted(context)
            if IMediaAsset.providedBy(adobj):
                from loops.media.browser.asset import MediaAssetView
                view = MediaAssetView(context, self.request)
                return view.show(useAttachment)
        ti = IType(context).typeInterface
        if ti is not None:
            context = ti(context)
        data = context.data
        if useAttachment:
            filename = adapted(self.context).localFilename or getName(self.context)
            filename = NameChooser(getParent(self.context)).normalizeName(filename)
            response.setHeader('Content-Disposition',
                               'attachment; filename=%s' % filename)
        response.setHeader('Content-Length', len(data))
        if ct.startswith('text/') and not useAttachment:
            response.setHeader('Content-Type', 'text/html')
            return self.renderText(data, ct)
        response.setHeader('Content-Type', ct)
        # set Last-Modified header
        modified = self.modifiedRaw
        if modified:
            format = '%a, %d %b %Y %H:%M:%S %Z'
            if getattr(modified, 'tzinfo', None) is None:
                format = format[:-3] + ' GMT'
            response.setHeader('Last-Modified', modified.strftime(format))
        return data

    def renderText(self, text, contentType):
        if contentType == 'text/restructured' and wikiLinksActive(self.loopsRoot):
            # TODO: make this more flexible/configurable
            wm = LoopsWikiManager(self.loopsRoot)
            wm.setup()
            wiki = LoopsWiki('loops')
            wiki.__parent__ = self.loopsRoot
            wiki.__name__ = 'wiki'
            wm.addWiki(wiki)
            #wp = wiki.createPage(getName(self.context))
            wp = wiki.addPage(LoopsWikiPage(self.context))
            wp.text = text
            #print wp.wiki.getManager()
            #return util.toUnicode(wp.render(self.request))
        return super(ResourceView, self).renderText(text, contentType)

    def download(self):
        """ Force download, e.g. of a PDF file """
        return self.show(True)

    @property
    def viewable(self):
        return True
        ct = self.context.contentType
        return (ct.startswith('image/') or
                    ct in ('application/pdf', 'application/x-pdf'))

    # actions

    def getPortletActions(self, page=None, target=None):
        if canWrite(target.context, 'data'):
            return actions.get('portlet', ['edit_object'], view=self, page=page,
                               target=target)
        return []

    def getObjectActions(self, page=None, target=None):
        acts = ['info']
        acts.extend('state.' + st.statesDefinition for st in self.states)
        if self.globalOptions('organize.allowSendEmail'):
            acts.append('send_email')
        if self.xeditable:
            acts.append('external_edit')
        return actions.get('object', acts, view=self, page=page, target=target)

    actions = dict(portlet=getPortletActions, object=getObjectActions)

    # relations

    def isHidden(self, pr):
        hideRoles = None
        options = component.queryAdapter(adapted(pr.first), IOptions)
        if options is not None:
            hideRoles = options('hide_for', None)
        if not hideRoles:
            hideRoles = IOptions(adapted(pr.first.conceptType))('hide_for', None)
        if hideRoles is not None:
            principal = self.request.principal
            if (IUnauthenticatedPrincipal.providedBy(principal) and
                'zope.Anonymous' in hideRoles):
                return True
            roles = getRolesForPrincipal(principal.id, self.context)
            for r in roles:
                if r in hideRoles:
                    return True
        return False

    #@Lazy
    def conceptsForPortlet(self):
        return [p for p in self.relatedConcepts() if not self.isHidden(p.relation)]

    def relatedConcepts(self):
        for c in self.concepts():
            if c.isProtected:
                continue
            yield c

    def concepts(self):
        for r in self.context.getConceptRelations():
            yield ConceptRelationView(r, self.request)

    def clients(self):
        for node in self.context.getClients():
            yield NodeView(node, self.request)


class ResourceRelationView(ResourceView, BaseRelationView):

    __init__ = BaseRelationView.__init__

    getActions = ResourceView.getActions


class ResourceConfigureView(ResourceView, ConceptConfigureView):

    #def __init__(self, context, request):
    #    # avoid calling ConceptView.__init__()
    #    ResourceView.__init__(self, context, request)

    def update(self):
        request = self.request
        action = request.get('action')
        if action is None:
            return True
        if action == 'create':
            self.createAndAssign()
            return True
        tokens = request.get('tokens', [])
        for token in tokens:
            parts = token.split(':')
            cToken = parts[0]
            if len(parts) > 1:
                relToken = parts[1]
            concept = self.loopsRoot.loopsTraverse(cToken)
            if action == 'assign':
                predicate = request.get('predicate') or None
                order = int(request.get('order') or 0)
                relevance = float(request.get('relevance') or 1.0)
                if predicate:
                    predicate = removeSecurityProxy(
                                    self.loopsRoot.loopsTraverse(predicate))
                self.context.assignConcept(removeSecurityProxy(concept), predicate,
                                           order, relevance)
            elif action in ('remove',):
                predicate = self.loopsRoot.loopsTraverse(relToken)
                if 'form.button.submit' in request:
                    if predicate != self.typePredicate:
                        self.context.deassignConcept(concept, [predicate])
                elif 'form.button.change_relations' in request:
                    order = request.get('order.' + token)
                    relevance = request.get('relevance.' + token)
                    for r in self.context.getConceptRelations([predicate], concept):
                        r.order = int(order or 0)
                        r.relevance = float(relevance or 1.0)
        return True

    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        searchType = request.get('searchType', None)
        result = []
        if searchTerm or searchType != 'none':
            criteria = {}
            if searchTerm:
                criteria['loops_title'] = searchTerm
            if searchType:
                if searchType.endswith('*'):
                    start = searchType[:-1]
                    end = start + '\x7f'
                else:
                    start = end = searchType
                criteria['loops_type'] = (start, end)
            cat = component.getUtility(ICatalog)
            result = cat.searchResults(**criteria)
            # TODO: can this be done in a faster way?
            result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        else:
            result = self.loopsRoot.getConceptManager().values()
        if searchType == 'none':
            result = [r for r in result if r.conceptType is None]
        return self.viewIterator(result)


class DocumentView(ResourceView):

    @property
    def macro(self):
        return ResourceView.template.macros['render']

    @Lazy
    def view(self): return self

    def render(self):
        """ Return the rendered content (data) of the context object.
        """
        self.recordAccess('render', target=self.uniqueId)
        ctx = adapted(self.context)
        text = ctx.data
        contentType = ctx.contentType
        return self.renderText(ctx.data, ctx.contentType)

    @Lazy
    def inlineEditable(self):
        return (self.inlineEditingActive
                and self.context.contentType == 'text/html'
                and canWrite(self.context, 'data'))


class ExternalEditorView(ExternalEditorView, BaseView):
    # obsolete, base class is used immediately

    def load(self, url=None):
        #context = removeSecurityProxy(self.context)
        context = self.context
        self.recordAccess('external_edit', target=self.uniqueId)
        data = adapted(context).data
        r = []
        context = removeSecurityProxy(context)
        r.append('url:' + (url or absoluteURL(context, self.request)))
        r.append('content_type:' + str(context.contentType))
        r.append('meta_type:' + '.'.join((context.__module__, context.__class__.__name__)))
        auth = self.request.get('_auth')
        if auth:
            print 'ExternalEditorView: auth = ', auth
            if auth.endswith('\n'):
                auth = auth[:-1]
            r.append('auth:' + auth)
        cookie = self.request.get('HTTP_COOKIE','')
        if cookie:
            r.append('cookie:' + cookie)
        r.append('')
        r.append(data)
        result = '\n'.join(r)
        self.setHeaders(len(result))
        return fromUnicode(result)


class NoteView(DocumentView):

    @property
    def macro(self):
        return ResourceView.template.macros['render_note']

    @property
    def linkUrl(self):
        ad = self.typeAdapter
        return ad and ad.linkUrl or ''

