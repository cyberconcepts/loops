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

from zope.cachedescriptors.property import Lazy
from zope.app import zapi
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.browser.contents import JustContents
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.intid.interfaces import IIntIds
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import ITypeManager
from loops.interfaces import IConcept, IResource, IDocument, IMediaAsset
from loops.resource import MediaAsset
from loops import util
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView


class NodeView(BaseView):

    template = ViewPageTemplateFile('node_macros.pt')
    macro = template.macros['content']

    @Lazy
    def item(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is not None:
            # .target.... traversal magic
            return zapi.getMultiAdapter((target, self.request))
        return self.page

    @Lazy
    def page(self):
        page = self.context.getPage()
        return page is not None and NodeView(page, self.request) or None

    @Lazy
    def textItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getTextItems()]
            

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
            return zapi.getMultiAdapter((obj, self.request))

    def renderTarget(self):
        target = self.target
        return target is not None and target.render() or u''

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def bodyMacro(self):
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
    def menu(self):
        menu = self.context.getMenu()
        return menu is not None and NodeView(menu, self.request) or None

    @Lazy
    def menuItems(self):
        return [NodeView(child, self.request)
                    for child in self.context.getMenuItems()]

    @Lazy
    def parents(self):
        return zapi.getParents(self.context)

    @Lazy
    def nearestMenuItem(self):
        if self.context.isMenuItem():
            return self.context
        for p in self.parents:
            if p.isMenuItem():
                return p

    def selected(self, item):
        return item.context == self.nearestMenuItem

    def active(self, item):
        return item.context == self.context or item.context in self.parents
            
    def targetDefaultView(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is None:
            target = self.targetObject
        if target is not None:
            targetView = zapi.getMultiAdapter((target, self.request),
                    name=zapi.getDefaultViewName(target, self.request))
            return targetView()
        return u''

    def targetId(self):
        target = self.request.annotations.get('loops.view', {}).get('target')
        if target is None:
            target = self.targetObject
        if target is not None:
            return zapi.getUtility(IIntIds).getId(target)


class ConfigureView(NodeView):
    """ An editing view for configuring a node, optionally creating
        a target object.
    """

    def __init__(self, context, request):
        #self.context = context
        self.context = removeSecurityProxy(context)
        self.request = request

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
        notify(ObjectCreatedEvent(target))
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

