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
Definition of the Task class.

$Id$
"""

from zope.interface import implements
from zope.app.container.ordered import OrderedContainer

from interfaces import ITask


class Task(OrderedContainer):

    implements(ITask)

    title = u''


    def __init__(self):
        OrderedContainer.__init__(self)
        self._subtasks = []
        self._parentTasks = []
        self._resourceAllocs = {}

    # subtasks:

    def getSubtasks(self, taskTypes=None):
        return tuple(self._subtasks)

    def getParentTasks(self, taskTypes=None):
        return tuple(self._parentTasks)

    def assignSubtask(self, task):
        self._subtasks.append(task)
        task._parentTasks.append(self)

    def createSubtask(self, taskType=None, container=None, name=None):
        container = container or self.__parent__
        task = Task()
        name = name or self._createTaskName()
        container[name] = task
        self.assignSubtask(task)
        return task

    def deassignSubtask(self, task):
        self._subtasks.remove(task)
        task._parentTasks.remove(self)

    # resources:

    def getAllocatedResources(self, allocTypes=None, resTypes=None):
        from sets import Set
        allocs = self._resourceAllocs
        res = Set()
        for at in allocs.keys():
            if allocTypes is None or at in allocTypes:
                res.union_update(allocs[at])
        return tuple(res)

    def allocateResource(self, resource, allocType=None):
        allocType = allocType or 'standard'
        allocs = self._resourceAllocs
        rList = allocs.get(allocType, [])
        rList.append(resource)
        allocs[allocType] = rList
        resource._updateAllocations(self, allocType)

    def createAndAllocateResource(self, resourceType='Resource', allocType='standard',
                                  container=None, id=None):
        return None

    def deallocateResource(self, resource):
        pass

    def allocatedUserIds(self):
        return ()

    def getAllocType(self, resource):
        return 'standard'

    def getAllAllocTypes(self):
        return ('standard',)


    # Helper methods:

    def _createTaskName(self):
        prefix = 'tsk'
        last = max([ int(n[len(prefix):]) for n in self.__parent__.keys() ] or [1])
        return prefix + str(last+1)
