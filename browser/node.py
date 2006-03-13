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
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.app.event.objectevent import ObjectCreatedEvent
#import zope.configuration.name
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import ITypeManager
from loops.interfaces import IConcept, IDocument, IMediaAsset
from loops.resource import MediaAsset
from loops.target import getTargetTypes, getTargetTypesForSearch
from loops import util
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView


class NodeView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def title(self):
        return self.context.title

    @Lazy
    def nodeType(self):
        return self.context.nodeType

    @Lazy
    def url(self):
        return zapi.absoluteURL(self.context, self.request)

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
    def modified(self):
        """ get date/time of last modification
        """
        dc = ICMFDublinCore(self.context)
        d = dc.modified or dc.created
        return d and d.strftime('%Y-%m-%d %H:%M') or ''

    @Lazy
    def target(self):
        return self.context.target

    def renderTarget(self):
        target = self.target
        if target is not None:
            targetView = zapi.getMultiAdapter((target, self.request),
                    name=zapi.getDefaultViewName(target, self.request))
            return targetView()
        return u''

    def renderTargetBody(self):
        target = self.target
        if target is not None:
            targetView = zapi.getMultiAdapter((target, self.request))
            return targetView.render()
        return u''

    @Lazy
    def page(self):
        page = self.context.getPage()
        return page is not None and NodeView(page, self.request) or None

    def textItems(self):
        for child in self.context.getTextItems():
            yield NodeView(child, self.request)

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def bodyMacro(self):
        target = self.target
        if target is None or IDocument.providedBy(target):
            return 'textbody'
        if IConcept.providedBy(target): # TODO...
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

    def menuItems(self):
        for child in self.context.getMenuItems():
            yield NodeView(child, self.request)

    def selected(self, item):
        return item.context == self.context


class ConfigureView(BaseView):
    """ An editing view for configuring a node, optionally creating
        a target object.
    """

    def __init__(self, context, request):
        #self.context = context
        self.context = removeSecurityProxy(context)
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @property
    def target(self):
        target = self.context.target
        if target is not None:
            if IConcept.providedBy(target):
                return ConceptView(target, self.request)
            return BaseView(target, self.request)
        return None

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
            #if IConcept.providedBy(o):
            #    yield ConceptView(o, request)
            #else:
            #    yield BaseView(o, request)

