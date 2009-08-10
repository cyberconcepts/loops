#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Layout node + instance implementations.

$Id$
"""

from logging import getLogger
from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.traversing.api import getName

from cybertools.composer.layout.base import Layout, LayoutInstance
from cybertools.composer.layout.interfaces import ILayoutInstance
from loops.common import adapted
from loops.layout.interfaces import ILayoutNode, ILayoutNodeContained
from loops.view import Node


logger = getLogger('loops.layout')


class LayoutNode(Node):

    pageName = u''

    implements(ILayoutNode, ILayoutNodeContained)


# layout instances

class NodeLayoutInstance(LayoutInstance):

    adapts(ILayoutNode)

    @Lazy
    def viewAnnotations(self):
        return self.view.request.annotations.get('loops.view', {})

    @Lazy
    def target(self):
        return adapted(self.context.target)

    @Lazy
    def targetView(self):
        request = self.view.request
        view = component.getMultiAdapter((self.target, request), name='layout')
        view.node = self.context
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
        obj = self.target.context
        tp = obj.getType()
        found = False
        topLevelLayout = self.context.getMenu()
        for n in obj.getClients() + tp.getClients():
            if not ILayoutNode.providedBy(n):
                continue
            if n.nodeType == 'info' and n.viewName in names:
                if pageName != (n.pageName or '').strip():
                    continue
                if n.getMenu() != topLevelLayout:
                    continue
                layout = region.layouts[n.viewName]
                li = component.getAdapter(n, ILayoutInstance,
                                          name=layout.instanceName)
                li.template = layout
                result.append(li)
                found = True
        if not found:
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
        return target
