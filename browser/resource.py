#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.app import zapi
from zope.app.catalog.interfaces import ICatalog
from zope.dublincore.interfaces import ICMFDublinCore
from zope.app.form.browser.textwidgets import FileWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.formlib.form import FormFields
from zope.formlib.interfaces import DISPLAY_UNWRITEABLE
from zope.proxy import removeAllProxies
from zope.schema.interfaces import IBytes
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import IType
from loops.browser.common import EditForm, BaseView, Action
from loops.browser.concept import ConceptRelationView, ConceptConfigureView
from loops.browser.node import NodeView, node_macros
from loops.browser.util import html_quote
from loops.interfaces import IBaseResource, IDocument, IMediaAsset, ITextDocument
from loops.interfaces import ITypeConcept
from loops.versioning.browser import version_macros
from loops.versioning.interfaces import IVersionable

renderingFactories = {
    'text/plain': 'zope.source.plaintext',
    'text/stx': 'zope.source.stx',
    'text/structured': 'zope.source.stx',
    'text/rest': 'zope.source.rest',
    'text/restructured': 'zope.source.rest',
}


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
    form_fields = FormFields(IMediaAsset)


class ResourceView(BaseView):

    template = ViewPageTemplateFile('resource_macros.pt')

    @property
    def macro(self):
        if 'image/' in self.context.contentType:
            return self.template.macros['image']
        else:
            return self.template.macros['download']

    def __init__(self, context, request):
        super(ResourceView, self).__init__(context, request)
        if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
            cont = self.controller
            if cont is not None and list(self.relatedConcepts()):
                cont.macros.register('portlet_right', 'related', title='Related Items',
                             subMacro=self.template.macros['related'],
                             position=0, info=self)
                versionable = IVersionable(self.context, None)
                if versionable is not None and len(versionable.versions) > 1:
                        cont.macros.register('portlet_right', 'versions',
                                title='Version ' + versionable.versionId,
                                subMacro=version_macros.macros['portlet_versions'],
                                position=1, info=self)

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
        #if ct.startswith('text/') and ct != 'text/rtf':
        ti = IType(context).typeInterface
        if not ti or issubclass(ti, ITextDocument):
            return DocumentView(context, self.request)
        return self

    def show(self, useAttachment=False):
        """ show means: "download"..."""
        #data = self.openForView()
        #response.setHeader('Content-Disposition',
        #                   'attachment; filename=%s' % zapi.getName(self.context))
        #return data
        context = self.context
        ti = IType(context).typeInterface
        if ti is not None:
            context = ti(context)
        data = context.data
        response = self.request.response
        response.setHeader('Content-Type', context.contentType)
        response.setHeader('Content-Length', len(data))
        ct = context.contentType
        if useAttachment or (not ct.startswith('image/') and ct != 'application/pdf'):
            response.setHeader('Content-Disposition',
                            'attachment; filename=%s' % zapi.getName(self.context))
        return data

    def download(self):
        """ Force download, e.g. of a PDF file """
        return self.show(True)

    def getActions(self, category='object'):
        renderer = node_macros.macros['external_edit']
        node = self.request.annotations.get('loops.view', {}).get('node')
        if node is not None:
            nodeView = NodeView(node, self.request)
            url = nodeView.virtualTargetUrl
        else:
            url = self.url
        return [Action(renderer, url)]

    def concepts(self):
        for r in self.context.getConceptRelations():
            yield ConceptRelationView(r, self.request)

    def relatedConcepts(self):
        for c in self.concepts():
            if c.isProtected: continue
            yield c

    def clients(self):
        for node in self.context.getClients():
            yield NodeView(node, self.request)


class ResourceConfigureView(ResourceView, ConceptConfigureView):

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
            token = parts[0]
            if len(parts) > 1:
                relToken = parts[1]
            concept = self.loopsRoot.loopsTraverse(token)
            if action == 'assign':
                predicate = request.get('predicate') or None
                if predicate:
                    predicate = removeSecurityProxy(
                                    self.loopsRoot.loopsTraverse(predicate))
                self.context.assignConcept(removeSecurityProxy(concept), predicate)
            elif action == 'remove':
                predicate = self.loopsRoot.loopsTraverse(relToken)
                self.context.deassignConcept(concept, [predicate])
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
            cat = zapi.getUtility(ICatalog)
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
        text = self.context.data
        contentType = self.context.contentType
        typeKey = renderingFactories.get(contentType, None)
        if typeKey is None:
            if contentType == u'text/html':
                return text
            return u'<pre>%s</pre>' % html_quote(text)
        source = zapi.createObject(typeKey, text)
        view = zapi.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    @Lazy
    def inlineEditable(self):
        return (self.inlineEditingActive
                and self.context.contentType == 'text/html'
                and canWrite(self.context, 'data'))


class NoteView(DocumentView):

    @property
    def macro(self):
        return ResourceView.template.macros['render_note']

    @property
    def linkUrl(self):
        ad = self.typeAdapter
        return ad and ad.linkUrl or ''

