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
loops interface definitions.

$Id: interfaces.py $
"""

from zope.app.container.interfaces import IOrderedContainer

from zope.schema import TextLine


class IEntity(IOrderedContainer):
    """ Common base class of the Task and Resource classes.
    """

    def getRelations(relationships=None):
        """ Return a list of target objects from relations assiociated
            with this Entity, possibly restricted to the relationships given.
        """

    def getReverseRelations(relationships=None):
        """ Return a list of source objects from relations directed at
            this Entity as the target, possibly restricted to the relationships
            given.
        """

class DummyIEntity:
    def getRelation(target, relationship=None):
        """ Return the relation object specified by target and relationship.
        """

    def addRelation(target, relationship, **props):
        """ Create a new relation object with relationship to target
            and assign it to self.
            If supported by relationship additional properties may be
            given as keyword parameters.
            Return relation object.
        """

    def removeRelation(target, relationship):
        """ Remove the relation to target with relationship from self.
        """

    def getController():
        """ Return the LoopsController object of this Entity, typically
            the parent LoopsManager object or the portal_loops Tool.
        """


class ITask(IEntity):
    """ A Task is a scheduled piece of work.
        Resources may be allocated to a Task.
        A Task may depend on subtasks.
    """

    title = TextLine(
        title=u'Title',
        description=u'Name or short title of the task',
        default=u'',
        required=True)

class DummyITask:
    def getSubtasks(taskTypes=None):
        """ Return a list of subtasks of self,
            possibly restricted to the task types given.
        """

    def createSubtask(taskType=None, container=None, id=None, **props):
        """ Create a new task with id in container and assign it to self as a subtask.
            container defaults to parent of self.
            id will be generated if not given.
            Return the relation object that leads to the subtask
            (fetch the subtask via relation.getTarget()).
        """

    def assignSubtask(task):
        """ Assign an existing task to self as a subtask.
            Return the relation object that leads to the subtask.
        """

    def deassignSubtask(task):
        """ Remove the subtask relation to task from self.
        """

    def getParentTasks():
        """ Return a list of tasks to which self has a subtask relationship.
        """

    def getAllocatedResources(allocTypes=None, resTypes=None):
        """ Return a list of resources allocated to self,
            possibly restricted to the allocation types and
            target resource types given.
        """

    def allocateResource(resource, allocType=None, **props):
        """ Allocate resource to self. A special allocation type may be given.
            Additional properties may be given as keyword parameters.
            Return relation object that implements the allocation reference.
        """

    def deallocateResource(resource):
        """ Deallocate from self the resource allocated.
        """

    def allocatedUserIds():
        """ Returns list of user IDs of allocated Person objects that are portal members.
            Used by catalog index 'allocUserIds'.
        """

    def getAllocType(resource):
        """ Return the allocation type for the resource given. Raise a
            ValueException if resource is not allocated to self.
        """

    def getAllAllocTypes():
        """ Return a tuple with all available allocation types defined
            in the LoopsController object that is responsible for self.
        """
