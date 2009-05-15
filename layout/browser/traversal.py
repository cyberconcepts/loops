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
Layout node traversers.

$Id$
"""

from zope.app.container.traversal import ItemTraverser
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.publisher.interfaces import NotFound

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
                target = traverser.publishTraverse(self, request, name)
                if target is not None:
                    viewAnnotations['target'] = target
                    tv = component.getMultiAdapter((target, request), name='layout')
                    viewAnnotations['targetView'] = tv
                    return self.context
        obj = None
        # for name, tr in component.getAdapters(self.context, IPublishTraverse):
        #     if name:
        #         obj = tr.publishTraverse(request, name)
        if obj is None:
            try:
                obj = super(NodeTraverser, self).publishTraverse(request, name)
            except NotFound, e:
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

