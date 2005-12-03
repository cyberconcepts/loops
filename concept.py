#
#  Copyright (c) 2005 Helmut Merz helmutm@cy55.de
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
from zope.app.copypastemove import ObjectCopier
from zope.app import zapi
from zope.schema.fieldproperty import FieldProperty
from zope.component.interfaces import IFactory

from cybertools.relation.interfaces import IRelationsRegistry
from cybertools.relation import DyadicRelation

#from relation import Relation, Relations
from resource import Resource
from interfaces import ITask

from copy import copy


class SubtaskRelation(DyadicRelation):
    """ Relation of a first task (the parent task) to a second task
        (the subtask).
    """


class Task(OrderedContainer):

    implements(ITask)

    title = u''
    qualifier = u''
    priority = FieldProperty(ITask['priority'])

    def __init__(self, name=None, title=u''):
        OrderedContainer.__init__(self)
        if name:
            self.__name__ = name
        if title:
            self.title = title

    # subtasks:

    def getSubtasks(self, taskTypes=None):
        registry = zapi.getUtility(IRelationsRegistry)
        return [r.second
                for r in registry.query(relationship=SubtaskRelation,
                                        first=self)]
        # TODO: sort according to priority

    def getParentTasks(self, taskTypes=None):
        registry = zapi.getUtility(IRelationsRegistry)
        return [r.first
                for r in registry.query(relationship=SubtaskRelation,
                                        second=self)]

    def assignSubtask(self, task):
        registry = zapi.getUtility(IRelationsRegistry)
        registry.register(SubtaskRelation(self, task))
        # TODO (?): avoid duplicates

    def createSubtask(self, taskType=None, container=None, name=None):
        container = container or zapi.getParent(self)
        task = Task()
        name = name or task._createTaskName(container)
        container[name] = task
        self.assignSubtask(task)
        return task

    def deassignSubtask(self, task):
        hits = [ r for r in self._subtasks if r._target == task ]
        if hits:
            self._subtasks.remove(hits[0])
            task._parentTasks.remove(hits[0])

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

    # resource constraint stuff:

    def isResourceAllowed(self, resource, rcDontCheck=None):
        rc = self.resourceConstraints
        if not rc:
            return True
        for c in rc:
            if rcDontCheck and c == rcDontCheck:  # don't check constraint already checked
                continue
            # that's too simple, we must check all constraints for constraintType:
            if not c.isResourceAllowed(resource):
                return False
        return True

    def getCandidateResources(self):
        rc = self.resourceConstraints
        if not rc:
            return ()
        for c in rc:
            candidates = c.getAllowedResources()
            if candidates is not None:
                return tuple([ r for r in candidates if self.isResourceAllowed(r, c) ])
        return ()

    def getAllowedResources(self, candidates=None):
        rc = self.resourceConstraints
        if not rc:
            return None
        if candidates is None:
            result = self.getCandidateResources()
            # Empty result means: can't tell
            return result and result or None
        return tuple([ r for r in candidates if self.isResourceAllowed(r) ])

    def isValid(self, checkSubtasks=True):
        if self.resourceConstraints is not None:
            for r in self.getAllocatedResources():
                if not self.isResourceAllowed(r):
                    return False
        if checkSubtasks:
            for t in self.getSubtasks():
                if not t.isValid():
                    return False
        return True

    # Task object as prototype:

    def copyTask(self, targetContainer=None):
        targetContainer = targetContainer or zapi.getParent(self)
        newName = self._createTaskName(targetContainer)
        newTask = copy(self)
        targetContainer[newName] = newTask
        subtasks = self.getSubtasks() 
        newTask._subtasks.clear()
        for st in subtasks:
            newSt = st.copyTask(targetContainer)
            newSt._parentTasks.clear()
            newTask.assignSubtask(newSt)
        return newTask

    # Helper methods:

    def _createTaskName(self, container=None):
        prefix = 'tsk'
        container = container or zapi.getParent(self)
        last = max([ int(n[len(prefix):]) for n in container.keys() ] or [0])
        return prefix + str(last+1)
