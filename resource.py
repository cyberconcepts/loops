#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
Definition of the Resource class.

$Id$
"""

from zope.interface import implements
from zope.app.container.ordered import OrderedContainer

from interfaces import IResource


class Resource(OrderedContainer):

    implements(IResource)

    title = u''


    def __init__(self):
        OrderedContainer.__init__(self)
        self._allocations = {}


    def getTasksAllocatedTo(self, allocTypes=None, taskTypes=None):
        from sets import Set
        allocs = self._allocations
        res = Set()
        for at in allocs.keys():
            if allocTypes is None or at in allocTypes:
                res.union_update(allocs[at])
        return tuple(res)


    # Helper methods:

    def _updateAllocations(self, task, allocType):
        #called by Task.allocateResource
        tList = self._allocations.get(allocType, [])
        tList.append(task)
        self._allocations[allocType] = tList

    def _createResourceName(self):
        prefix = 'rsc'
        last = max([ int(n[len(prefix):]) for n in self.__parent__.keys() ] or [1])
        return prefix + str(last+1)
