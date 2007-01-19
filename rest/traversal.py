# -*- coding: UTF-8 -*-
# -*- Mode: Python; py-indent-offset: 4 -*-
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

$Id$
"""

from zope import component
from zope.component import adapts
from zope.app.container.traversal import ItemTraverser
from zope.publisher.interfaces.browser import IBrowserRequest

from loops.interfaces import ILoops
from loops import util
from loops.rest.common import IRESTView


class LoopsTraverser(ItemTraverser):

    adapts(ILoops, IBrowserRequest)

    restProperties = ('startObject', 'typePredicate',)

    def publishTraverse(self, request, name):
        if name in self.restProperties:
            obj = getattr(self, name)
            return component.getMultiAdapter((obj, request), IRESTView)
        if name.isdigit():
            obj = util.getObjectForUid(int(name))
            return component.getMultiAdapter((obj, request), IRESTView)
        return super(LoopsTraverser, self).publishTraverse(request, name)

    @property
    def startObject(self):
        cm = self.context.getConceptManager()
        return cm.get('domain', cm.getTypeConcept())
