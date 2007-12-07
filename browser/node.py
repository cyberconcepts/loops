#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
View class for Node objects.

$Id$
"""

from zope import component, interface, schema
from zope.cachedescriptors.property import Lazy
from zope.app import zapi
from zope.annotation.interfaces import IAnnotations
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.browser.contents import JustContents
from zope.app.container.browser.adding import Adding
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.lifecycleevent import Attributes
from zope.formlib.form import Form, FormFields
from zope.formlib.namedtemplate import NamedTemplate
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.ajax import innerHtml
from cybertools.browser import configurator
from cybertools.browser.view import GenericView
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.xedit.browser import ExternalEditorView
from loops.interfaces import IConcept, IResource, IDocument, IMediaAsset, INode
from loops.interfaces import IViewConfiguratorSchema
from loops.resource import MediaAsset
from loops import util
from loops.util import _
from loops.browser.action import Action, DialogAction, TargetAction
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.versioning.util import getVersion


node_macros = ViewPageTemplateFile('node_macros.pt')


class NodeView(BaseView):

    _itemNum = 0

    #template = NamedTemplate('loops.node_macros')
    template = node_macros

    @Lazy
    def macro(self):
        return self.template.macros['content']

    def setupController(self):
        cm = self.controller.macros
        cm.register('css', identifier='loops.css', resourceName='loops.css',
                    media='all', position=3)
        cm.register('js', 'loops.js', resourceName='loops.js')
        #cm.register('js', 'loops.js', resourceName='loops1.js')
        cm.register('portlet_left', 'navigation', title='Navigation',
                    subMacro=node_macros.macros['menu'])
        #if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
        if canWrite(self.context, 'title'):
            #cm.register('portlet_right', 'clipboard', title='Clipboard',
            #            subMacro=self.template.macros['clipboard'])
            # this belongs to loops.organize; how to register portlets
            # from sub- (other) packages?
            # see controller / configurator: use multiple configurators;
            # register additional configurators (adapters) from within package.
            cm.register('portlet_right', 'actions', title=_(u'Actions'),
                        subMacro=node_macros.macros['actions'])

    @Lazy
    def view(self):
        viewName = self.request.get('loops.viewName') or self.context.viewName
        if viewName:
            adapter = component.queryMultiAdapter(
                            (self.context, self.request), name=viewName)
            if adapter is not None:
                return adapter
        return self

    @Lazy
    def item(self):
        viewName = self.request.get('loops.viewName') or ''
        # was there a .target... element in the URL?
        #target = self.virtualTargetObject  # ignores page even for direktly assignd target
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is not None:
            basicView = zapi.getMultiAdapter((target, self.request), name=viewName)
            # xxx: obsolete when self.targetObject is virtual target:
            return basicView.view
        return self.page

    @Lazy
    def page(self):
        page = self.context.getPage()
        return page is not None and NodeView(page, self.request).view or None

    @Lazy
    def textItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getTextItems()]

    @Lazy
    def pageItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getPageItems()]

    @property
    def itemNum(self):
        self._itemNum += 1
        return self._itemNum

    @Lazy
    def nodeType(self):
        return self.context.nodeType

    def render(self, text=None):
        if text is None:
            text = self.context.body
        if not text:
            return u''
        if text.startswith('<'):  # seems to be HTML
            return text
        source = zapi.createObject(self.context.contentType, text)
        view = zapi.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    @Lazy
    def targetObject(self):
        # xxx: use virtualTargetObject
        #return self.virtualTargetObject
        target = self.context.target
        if target is not None:
            target = getVersion(target, self.request)
        return target

    @Lazy
    def targetObjectView(self):
        obj = self.targetObject
        if obj is not None:
            basicView = zapi.getMultiAdapter((obj, self.request))
            basicView._viewName = self.context.viewName
            return basicView.view

    @Lazy
    def targetUrl(self):
        t = self.targetObjectView
        if t is not None:
            return '%s/.target%s' % (self.url, t.uniqueId)
        return ''

    def renderTarget(self):
        target = self.targetObjectView
        return target is not None and target.render() or u''

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def bodyMacro(self):
        # TODO: replace by something like: return self.target.macroName
        target = self.targetObject
        if (target is None or IDocument.providedBy(target)
                or (IResource.providedBy(target) and
                    target.contentType.startswith('text/'))):
            return 'textbody'
        if IConcept.providedBy(target):
            return 'conceptbody'
        if IResource.providedBy(target) and target.contentType.startswith('image/'):
            return 'imagebody'
        return 'filebody'

    @Lazy
    def editable(self):
        return canWrite(self.context, 'body')

    # menu stuff

    @Lazy
    def menuObject(self):
        return self.context.getMenu()

    @Lazy
    def menu(self):
        menu = self.menuObject
        return menu is not None and NodeView(menu, self.request) or None

    @Lazy
    def topMenu(self):
        menu = self.menuObject
        parentMenu = None
        while menu is not None:
            parent = zapi.getParent(menu)
            if INode.providedBy(parent):
                parentMenu = parent.getMenu()
            if parentMenu is None or parentMenu is menu:
                return NodeView(menu, self.request)
            menu = parentMenu
        return menu is not None and NodeView(menu, self.request) or None

    @Lazy
    def headTitle(self):
        menuObject = self.menuObject
        if menuObject is not None and menuObject != self.context:
            prefix = super(NodeView, self.menu).headTitle + ' - '
        else:
            prefix = ''
        if self.virtualTarget:
            return prefix + self.virtualTarget.headTitle
        return prefix + super(NodeView, self).headTitle

    @Lazy
    def menuItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getMenuItems()]

    @Lazy
    def parents(self):
        return zapi.getParents(self.context)

    @Lazy
    def nearestMenuItem(self):
        menu = self.menuObject
        menuItem = None
        for p in [self.context] + self.parents:
            if not p.isMenuItem():
                menuItem = None
            elif menuItem is None:
                menuItem = p
            if p == menu:
                return menuItem
        return None

    def selected(self, item):
        return item.context == self.nearestMenuItem

    def active(self, item):
        return item.context == self.context or item.context in self.parents

    # virtual target support

    @Lazy
    def virtualTargetObject(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is None:
            target = self.context.target
            if target is not None:
                target = getVersion(target, self.request)
        return target

    def targetView(self, name='index.html', methodName='show'):
        target = self.virtualTargetObject
        if target is not None:
            ti = IType(target).typeInterface
            targetView = None
            if ti is not None:
                adapted = ti(target)
                targetView = component.queryMultiAdapter((adapted, self.request),
                        name=name)
            if targetView is None:
                targetView = component.getMultiAdapter((target, self.request),
                        name=name)
            if name == 'index.html' and hasattr(targetView, 'show'):
                return targetView.show()
            method = getattr(targetView, methodName, None)
            if method:
                return method()
            return targetView()
        return u''

    def targetDefaultView(self):
        target = self.virtualTargetObject
        if target is not None:
            name = zapi.getDefaultViewName(target, self.request)
            return self.targetView(name)
        return u''

    def targetDownload(self):
        return self.targetView('download.html', 'download')

    @Lazy
    def virtualTarget(self):
        obj = self.virtualTargetObject
        if obj is not None:
            basicView = zapi.getMultiAdapter((obj, self.request))
            basicView._viewName = self.context.viewName
            return basicView.view

    @Lazy
    def targetId(self):
        target = self.virtualTargetObject
        if target is not None:
            return BaseView(target, self.request).uniqueId

    @Lazy
    def virtualTargetUrl(self):
        targetId = self.targetId
        if targetId is not None:
            return '%s/.target%s' % (self.url, targetId)
        else:
            return self.url

    @Lazy
    def realTargetUrl(self):
        target = self.virtualTargetObject
        if target is not None:
            return BaseView(target, self.request).url

    # target viewing and editing support

    def getUrlForTarget(self, target):
        """ Return URL of given target view given as .targetXXX URL.
        """
        if isinstance(target, BaseView):
            return '%s/.target%s' % (self.url, target.uniqueId)
        else:
            return ('%s/.target%s' %
                (self.url, util.getUidForObject(target)))

    def getActions(self, category='object'):
        actions = []
        self.registerDojo()
        if category in self.actions:
            actions.extend(self.actions[category](self))
        target = self.virtualTarget
        if target is not None:
            actions.extend(target.getActions(category, page=self))
        return actions

    def getPortletActions(self):
        actions = []
        cmeUrl = self.conceptMapEditorUrl
        if cmeUrl:
            actions.append(Action(self, title='Edit Concept Map',
                      targetWindow='loops_cme',
                      description='Open concept map editor in new window',
                      url=cmeUrl))
        actions.append(DialogAction(self, title='Create Resource...',
                  description='Create a new resource object.',
                  page=self))
        return actions

    actions = dict(portlet=getPortletActions)

    @Lazy
    def hasEditableTarget(self):
        return IResource.providedBy(self.virtualTargetObject)

    @Lazy
    def inlineEditable(self):
        target = self.virtualTarget
        return target and target.inlineEditable or False

    def inlineEdit(self, id):
        self.registerDojo()
        cm = self.controller.macros
        jsCall = 'dojo.require("dojo.widget.Editor")'
        cm.register('js-execute', jsCall, jsCall=jsCall)
        return ('return inlineEdit("%s", "%s/inline_save")'
                                        % (id, self.virtualTargetUrl))

    def externalEdit(self):
        target = self.virtualTargetObject
        if target is None:
            target = self.context
            url = self.url
        else:
            ti = IType(target).typeInterface
            if ti is not None:
                target = ti(target)
                url = self.virtualTargetUrl
        return ExternalEditorView(target, self.request).load(url=url)

    # helper methods

    def registerDojoDialog(self):
        self.registerDojo()
        cm = self.controller.macros
        jsCall = 'dojo.require("dojo.widget.Dialog")'
        cm.register('js-execute', jsCall, jsCall=jsCall)


# inner HTML views

class InlineEdit(NodeView):
    """ Provides inline editor as inner HTML"""

    @Lazy
    def macro(self):
        return self.template.macros['inline_edit']

    def __call__(self):
        return innerHtml(self)

    @property
    def body(self):
        return self.virtualTargetObject.data

    def save(self):
        target = self.virtualTargetObject
        ti = IType(target).typeInterface
        if ti is not None:
            target = ti(target)
        data = self.request.form['editorContent']
        if type(data) != unicode:
            try:
                data = data.decode('ISO-8859-15')  # IE hack
            except UnicodeDecodeError:
                print 'loops.browser.node.InlineEdit.save():', data
                return
        #    data = data.decode('UTF-8')
        target.data = data
        notify(ObjectModifiedEvent(target, Attributes(IResource, 'data')))
        #versionParam = self.hasVersions and '?version=this' or ''
        #self.request.response.redirect(self.virtualTargetUrl + versionParam)
        return 'OK'


class xxxCreateObject(NodeView, Form):

    template = ViewPageTemplateFile('form_macros.pt')

    @property
    def macro(self): return self.template.macros['create']

    form_fields = FormFields(
        schema.TextLine(__name__='title', title=_(u'Title')),
        schema.Text(__name__='body', title=_(u'Body Text')),
        schema.TextLine(__name__='linkUrl', title=_(u'Link'), required=False),
    )

    title = _(u'Enter Note')
    form_action = 'create_note'

    def __init__(self, context, request):
        super(CreateObject, self).__init__(context, request)
        self.setUpWidgets()
        self.widgets['body'].height = 3

    def __call__(self):
        return innerHtml(self)


# special (named) views for nodes

class SpecialNodeView(NodeView):

    macroName = None # to be provided by subclass

    @Lazy
    def macro(self):
        return self.template.macros[self.macroName]

    @Lazy
    def view(self):
        return self


class ListPages(SpecialNodeView):
    macroName = 'listpages'

class ListResources(SpecialNodeView):
    macroName = 'listresources'

class ListChildren(SpecialNodeView):
    macroName = 'listchildren'


class ConfigureView(NodeView):
    """ An editing view for configuring a node, optionally creating
        a target object.
    """

    def __init__(self, context, request):
        #self.context = context
        self.context = removeSecurityProxy(context)
        self.request = request

    @Lazy
    def target(self):
        obj = self.targetObject
        if obj is not None:
            return zapi.getMultiAdapter((obj, self.request))

    def update(self):
        request = self.request
        action = request.get('action')
        if action is None or action == 'search':
            return True
        if action == 'create':
            return self.createAndAssign()
        if action == 'assign':
            token = request.get('token')
            if token:
                target = self.loopsRoot.loopsTraverse(token)
            else:
                target = None
            self.context.target = target
        # TODO: raise error
        return True

    def createAndAssign(self):
        form = self.request.form
        root = self.loopsRoot
        token = form.get('create.type', 'loops.resource.MediaAsset')
        type = ITypeManager(self.context).getType(token)
        factory = type.factory
        container = type.defaultContainer
        name = form.get('create.name', '')
        if not name:
            viewManagerPath = zapi.getPath(root.getViewManager())
            name = zapi.getPath(self.context)[len(viewManagerPath)+1:]
            name = name.replace('/', '.')
        # check for duplicates:
        num = 1
        basename = name
        while name in container:
            name = '%s-%d' % (basename, num)
            num += 1
        container[name] = removeSecurityProxy(factory())
        target = container[name]
        target.title = form.get('create.title', u'')
        if IConcept.providedBy(target):
            target.conceptType = type.typeProvider
        elif IResource.providedBy(target):
            target.resourceType = type.typeProvider
        notify(ObjectCreatedEvent(target))
        notify(ObjectModifiedEvent(target))
        self.context.target = target
        return True

    def targetTypes(self):
        return util.KeywordVocabulary([(t.token, t.title)
                        for t in ITypeManager(self.context).types])

    def targetTypesForSearch(self):
        general = [('loops:*', 'Any'), ('loops:concept:*', 'Any Concept'),
                   ('loops:resource:*', 'Any Resource'),]
        return util.KeywordVocabulary(general + [(t.tokenForSearch, t.title)
                        for t in ITypeManager(self.context).types])

    @Lazy
    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        searchType = request.get('searchType', None)
        if searchTerm or searchType:
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
            result = (list(self.loopsRoot.getConceptManager().values())
                    + list(self.loopsRoot.getResourceManager().values()))
        return list(self.viewIterator(result))

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            if o == self.context.target:
                continue
            yield BaseView(o, request)


class NodeAdding(Adding):

    def addingInfo(self):
        info = super(NodeAdding, self).addingInfo()
        #info.append({'title': 'Document',
        #             'action': 'AddLoopsNodeDocument.html',
        #             'selected': '',
        #             'has_custom_add_view': True,
        #             'description': 'This creates a node with an associated document'})
        return info


class ViewPropertiesConfigurator(object):

    interface.implements(IViewConfiguratorSchema)
    component.adapts(INode)

    def __init__(self, context):
        self.context = removeSecurityProxy(context)

    def setSkinName(self, skinName):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        setting['skinName'] = {'value': skinName}
        ann[configurator.ANNOTATION_KEY] = setting
    def getSkinName(self):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        return setting.get('skinName', {}).get('value', '')
    skinName = property(getSkinName, setSkinName)

    def setOptions(self, options):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        setting['options'] = {'value': options}
        ann[configurator.ANNOTATION_KEY] = setting
    def getOptions(self):
        ann = IAnnotations(self.context)
        setting = ann.get(configurator.ANNOTATION_KEY, {})
        return setting.get('options', {}).get('value', [])
    options = property(getOptions, setOptions)


class NodeViewConfigurator(configurator.ViewConfigurator):
    """ Take properties from next menu item...
    """

    @property
    def viewProperties(self):
        result = []
        for p in list(reversed(zapi.getParents(self.context))) + [self.context]:
            if not INode.providedBy(p) or p.nodeType != 'menu':
                continue
            ann = IAnnotations(p)
            propDefs = ann.get(configurator.ANNOTATION_KEY, {})
            if propDefs:
                result.extend([self.setupViewProperty(prop, propDef)
                                for prop, propDef in propDefs.items() if propDef])
        return result


