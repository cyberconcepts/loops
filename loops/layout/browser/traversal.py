# loops.layout.browser.traveral

""" Layout node traversers.
"""

from zope.app.container.traversal import ItemTraverser
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import NotFound, IPublishTraverse

from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops.layout.interfaces import ILayoutNode
from loops.versioning.util import getVersion
from loops import util


class NodeTraverser(ItemTraverser):

    adapts(ILayoutNode)

    def publishTraverse(self, request, name):
        viewAnnotations = request.annotations.setdefault('loops.view', {})
        viewAnnotations['node'] = self.context
        if name == '.loops':
            return self.context.getLoopsRoot()
        if name.startswith('.'):
            name = self.cleanUpTraversalStack(request, name)[1:]
            if name:
                if name.startswith('target'):
                    name = name[6:]
                if '-' in name:
                    name, ignore = name.split('-', 1)
                uid = int(name)
                target = util.getObjectForUid(uid)
            else:
                target = self.context.target
            if target is not None:
                target = getVersion(target, request)
                target = adapted(target, LanguageInfo(target, request))
                viewAnnotations['target'] = target
                tv = component.getMultiAdapter((target, request), name='layout')
                viewAnnotations['targetView'] = tv
                return self.context
        if self.context.target is not None:
            # check for specialized traverser
            traverser = IPublishTraverse(adapted(self.context.target), None)
            if traverser is not None:
                target = traverser.publishTraverse(request, name)
                if isinstance(target, BrowserView):
                    return target
                if target is not None:
                    viewAnnotations['target'] = target
                    tv = component.getMultiAdapter((target, request), name='layout')
                    viewAnnotations['targetView'] = tv
                    return self.context
        obj = None
        if obj is None:
            try:
                obj = super(NodeTraverser, self).publishTraverse(request, name)
            except NotFound:
                viewAnnotations['pageName'] = name
                return self.context
        return obj

    def cleanUpTraversalStack(self, request, name):
        traversalStack = request._traversal_stack
        while traversalStack and traversalStack[0].startswith('.'):
            # skip obsolete target references in the url
            name = traversalStack.pop(0)
        traversedNames = request._traversed_names
        if traversedNames:
            lastTraversed = traversedNames[-1]
            if lastTraversed.startswith('.') and lastTraversed != name:
                # let <base .../> tag show the current object
                traversedNames[-1] = name
        return name

