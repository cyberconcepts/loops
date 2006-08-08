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

from zope import component, interface
from zope.cachedescriptors.property import Lazy
from zope.app import zapi
from zope.app.annotation.interfaces import IAnnotations
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.browser.contents import JustContents
from zope.app.container.browser.adding import ContentAdding
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.intid.interfaces import IIntIds
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.formlib.namedtemplate import NamedTemplate
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.browser import configurator
from cybertools.typology.interfaces import ITypeManager
from loops.interfaces import IConcept, IResource, IDocument, IMediaAsset, INode
from loops.interfaces import IViewConfiguratorSchema
from loops.resource import MediaAsset
from loops import util
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView


class NodeView(BaseView):

    template = NamedTemplate('loops.node_macros')

    @Lazy
    def macro(self):
        return self.template.macros['content']
        #macroName = self.request.get('loops.viewName')
        #if not macroName:
        #    macroName = self.context.viewName or 'content'
        #return self.template.macros[macroName]

    @Lazy
    def view(self):
        viewName = self.request.get('loops.viewName') or self.context.viewName
        if viewName:
            adapter = component.queryMultiAdapter((self.context, self.request),
                                        interface.Interface, name=viewName)
            if adapter is not None:
                return adapter
        return self

    @Lazy
    def item(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        # was there a .target... element in the URL?
        if target is not None:
            basicView = zapi.getMultiAdapter((target, self.request))
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
        return self.context.target

    @Lazy
    def target(self):
        obj = self.targetObject
        if obj is not None:
            basicView = zapi.getMultiAdapter((obj, self.request))
            basicView._viewName = self.context.viewName
            return basicView.view

    @Lazy
    def targetUrl(self):
        t = self.target
        if t is not None:
            return '%s/.target%s' % (self.url, t.uniqueId)
        return ''

    def renderTarget(self):
        target = self.target
        return target is not None and target.render() or u''

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def bodyMacro(self):
        # ?TODO: replace by: return self.target.macroName
        target = self.targetObject
        if target is None or IDocument.providedBy(target):
            return 'textbody'
        if IConcept.providedBy(target):
            return 'conceptbody'
        if IMediaAsset.providedBy(target) and target.contentType.startswith('image/'):
            return 'imagebody'
        return 'filebody'

    @Lazy
    def editable(self):
        return canWrite(self.context, 'body')

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

    def targetDefaultView(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is None:
            target = self.targetObject
        if target is not None:
            name = zapi.getDefaultViewName(target, self.request)
            targetView = zapi.getMultiAdapter((target, self.request),
                    name=name)
            return targetView()
        return u''

    def targetId(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is None:
            target = self.targetObject
        if target is not None:
            return zapi.getUtility(IIntIds).getId(target)


class ListPages(NodeView):

    @Lazy
    def macro(self):
        return self.template.macros['listpages']

    @Lazy
    def view(self):
        return self


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


class NodeAdding(ContentAdding):

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


