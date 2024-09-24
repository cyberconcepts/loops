# loops.layout.base

""" Layout node + instance implementations.
"""

from logging import getLogger
from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implementer
from zope.traversing.api import getName

from cybertools.composer.layout.base import Layout, LayoutInstance
from cybertools.composer.layout.interfaces import ILayoutInstance
from loops.common import adapted, baseObject
from loops.layout.interfaces import ILayoutNode, ILayoutNodeContained
from loops.view import Node


logger = getLogger('loops.layout')


@implementer(ILayoutNode, ILayoutNodeContained)
class LayoutNode(Node):

    pageName = u''


# layout instances

class NodeLayoutInstance(LayoutInstance):

    adapts(ILayoutNode)

    targetViewName = 'layout'

    @Lazy
    def viewAnnotations(self):
        return self.view.request.annotations.get('loops.view', {})

    @Lazy
    def target(self):
        return adapted(self.context.target)

    @Lazy
    def targetView(self):
        request = self.view.request
        view = component.getMultiAdapter((self.target, request),
                                         name=self.targetViewName)
        #view.node = self.context
        view.layoutInstance = self
        return view


class SubnodesLayoutInstance(NodeLayoutInstance):

    adapts(ILayoutNode)

    def getLayouts(self, region):
        """ Return sublayout instances specified via subnodes of the current menu node.
        """
        if region is None:
            return []
        result = []
        menu = self.context.getMenu()
        subnodes = menu.getMenuItems()
        names = region.layouts.keys()
        for n in subnodes:
            if n.viewName in names:
                layout = region.layouts[n.viewName]
                li = component.getAdapter(n, ILayoutInstance,
                                          name=layout.instanceName)
                li.template = layout
                result.append(li)
        return result


class TargetLayoutInstance(NodeLayoutInstance):
    """ Associates a layout with all objects of a certain type.
    """

    adapts(ILayoutNode)

    def getLayouts(self, region):
        """ Return sublayout instances specified by the target object.
        """
        if region is None or self.target is None:
            return []
        result = super(TargetLayoutInstance, self).getLayouts(region)
        names = region.layouts.keys()
        pageName = self.viewAnnotations.get('pageName', u'')
        obj = baseObject(self.target)
        tp = obj.getType()
        #found = False
        currentRoot = self.context.getMenu()
        specifics = []
        defaults = []
        for n in obj.getClients() + tp.getClients():
            if not ILayoutNode.providedBy(n):
                continue
            if n.nodeType == 'info' and n.viewName in names:
                if pageName != (n.pageName or '').strip():
                    continue
                layoutRoot = n.getMenu()
                rootName = getName(layoutRoot)
                if rootName != 'default' and layoutRoot != currentRoot:
                    continue
                layout = region.layouts[n.viewName]
                li = component.getAdapter(n, ILayoutInstance,
                                          name=layout.instanceName)
                li.template = layout
                #result.append(li)
                #found = True
                if rootName == 'default':
                    defaults.append(li)
                else:
                    specifics.append(li)
        if specifics:
            result.extend(specifics)
        elif defaults:
            result.extend(defaults)
        #if not found:
        else:
            if self.template.defaultSublayout is None:
                logger.warn('No target layout found: pageName = %r, target = %r'
                                % (pageName, getName(obj)))
            else:
                layout = region.layouts.get(self.template.defaultSublayout)
                if layout is not None:
                    li = component.getAdapter(self.context, ILayoutInstance,
                                            name=layout.instanceName)
                    li.template = layout
                    result.append(li)
        return result

    @Lazy
    def target(self):
        target = self.viewAnnotations.get('target')
        if target is None:
            target = adapted(self.context.target)
            #self.viewAnnotations['target'] = target    # TODO: has to be tested!
        return target
