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

$Id$
"""

from zope.interface import Interface
from zope.app.container.interfaces import IOrderedContainer

from zope.schema import TextLine


class ITask(IOrderedContainer):
    """ A Task is a piece of work.

        Resources may be allocated to a Task.
        A Task may depend on subtasks.
    """

    title = TextLine(
        title=u'Title',
        description=u'Name or short title of the task',
        default=u'',
        required=True)

    def getSubtasks(taskTypes=None):
        """ Return a tuple of subtasks of self,
            possibly restricted to the task types given.
        """

    def assignSubtask(task):
        """ Assign an existing task to self as a subtask..
        """

    def getParentTasks():
        """ Return a tuple of tasks to which self has a subtask relationship.
        """

    def createSubtask(taskType=None, container=None, name=None):
        """ Create a new task with id in container and assign it to self as a subtask.
            container defaults to parent of self.
            name will be generated if not given.
            Return the new subtask.
        """

    def deassignSubtask(task):
        """ Remove the subtask relation to task from self.
        """

    def getAllocatedResources(allocTypes=None, resTypes=None):
        """ Return a tuple of resources allocated to self,
            possibly restricted to the allocation types and
            target resource types given.
        """

    def allocateResource(resource, allocType='standard'):
        """ Allocate resource to self. A special allocation type may be given.
        """

    def createAndAllocateResource(resourceType=None, allocType='standard',
                                  container=None, name=None):
        """ Allocate resource to self. A special allocation type may be given.
        """

    def deallocateResource(resource, allocTypes=None):
        """ Deallocate from self the resource given. If no allocTypes
            given all allocations to resource will be removed.
        """

    def allocatedUserIds():
        """ Returns tuple of user IDs of allocated Person objects that are portal members.
            Used by catalog index 'allocUserIds'.
        """

    def getAllocTypes(resource):
        """ Return the allocation types with which the resource given
            is allocated to self.
        """

    def getAllAllocTypes():
        """ Return a tuple with all available allocation types defined
            in the controller object that is responsible for self.
        """


class IResource(IOrderedContainer):
    """ A Resource is an object - a thing or a person - that may be
        allocated to one or more Task objects.
    """

    def getTasksAllocatedTo(allocTypes=None, taskTypes=None):
        """ Return a list of task to which self is allocated to,
            possibly restricted to the allocation types and
            source task types given.
        """


class IResourceConstraint(Interface):
    """ A ResourceConstraint governs which Resource objects may be
        allocated to a Task object.
    """

