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
Layout node traversers.

$Id$
"""

from zope.app.container.traversal import ItemTraverser
from zope.cachedescriptors.property import Lazy
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
        if name.startswith('.'):
            if len(name) > 1:
                if '-' in name:
                    name, ignore = name.split('-', 1)
                uid = int(name[1:])
                target = util.getObjectForUid(uid)
            else:
                target = self.context.target
            if target is not None:
                #viewAnnotations = request.annotations.setdefault('loops.view', {})
                viewAnnotations['node'] = self.context
                target = getVersion(target, request)
                target = adapted(target, LanguageInfo(target, request))
                viewAnnotations['target'] = target
                #return target
                return self.context
        try:
            obj = super(NodeTraverser, self).publishTraverse(request, name)
        except NotFound, e:
            viewAnnotations['pageName'] = name
            return self.context
        return obj
