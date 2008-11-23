#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.interface import implements

from cybertools.composer.layout.base import Layout, LayoutInstance
from cybertools.composer.layout.interfaces import ILayoutInstance
from loops.common import adapted
from loops.layout.interfaces import ILayoutNode, ILayoutNodeContained
from loops.view import Node


class LayoutNode(Node):

    pageName = u''

    implements(ILayoutNode, ILayoutNodeContained)


# layout instances

class NodeLayoutInstance(LayoutInstance):

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
        return view


class NavigationLayoutInstance(NodeLayoutInstance):

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

    def getLayouts(self, region):
        """ Return sublayout instances specified by the target object.
        """
        target = self.target
        pageName = self.viewAnnotations.get('pageName', u'')
        if region is None or target is None:
            return []
        result = []
        names = region.layouts.keys()
        tp = target.context.conceptType
        for n in tp.getClients():
            if n.nodeType == 'info' and n.viewName in names:
                if pageName != n.pageName:
                    continue
                layout = region.layouts[n.viewName]
                li = component.getAdapter(n, ILayoutInstance,
                                          name=layout.instanceName)
                li.template = layout
                result.append(li)
        # TODO: if not result: provide error info with names, pageName,
        #       info on client nodes
        return result

    @Lazy
    def target(self):
        target = self.viewAnnotations.get('target')
        if target is None:
            target = adapted(self.context.target)
        return target

