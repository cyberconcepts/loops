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
from zope.app import zapi

from resource import Resource
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
        container = container or zapi.getParent(self)
        task = Task()
        name = name or task._createTaskName(container)
        container[name] = task
        self.assignSubtask(task)
        return task

    def deassignSubtask(self, task):
        self._subtasks.remove(task)
        task._parentTasks.remove(self)

    # resource allocations:

    def getAllocatedResources(self, allocTypes=None, resTypes=None):
        from sets import Set
        allocs = self._resourceAllocs
        res = Set()
        for at in allocTypes or allocs.keys():
            res.union_update(allocs[at])
        if resTypes:
            res = [ r for r in res if r in resTypes ]
        return tuple(res)

    def allocateResource(self, resource, allocType='standard'):
        allocs = self._resourceAllocs
        rList = allocs.get(allocType, [])
        if resource not in rList:
            rList.append(resource)
        allocs[allocType] = rList
        resource._addAllocation(self, allocType)

    def createAndAllocateResource(self, resourceType=None, allocType='standard',
                                  container=None, name=None):
        container = container or zapi.getParent(self)
        rClass = resourceType or Resource
        resource = rClass()
        name = name or resource._createResourceName(container)
        container[name] = resource
        self.allocateResource(resource, allocType)
        return resource

    def deallocateResource(self, resource, allocTypes=None):
        allocs = self._resourceAllocs
        for at in allocTypes or allocs.keys():
            if resource in allocs[at]:
                allocs[at].remove(resource)
        resource._removeAllocations(self, allocTypes)

    def allocatedUserIds(self):
        return ()

    def getAllocTypes(self, resource):
        return ('standard',)

    def getAllAllocTypes(self):
        return ('standard',)


    # Helper methods:

    def _createTaskName(self, container=None):
        prefix = 'tsk'
        container = container or zapi.getParent(self)
        last = max([ int(n[len(prefix):]) for n in container.keys() ] or [1])
        return prefix + str(last+1)
