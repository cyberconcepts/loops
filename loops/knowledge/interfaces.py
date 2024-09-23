#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
Interfaces for knowledge management and elearning with loops.
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from cybertools.knowledge.interfaces import IKnowing, IRequirementProfile
from cybertools.knowledge.interfaces import IKnowledgeElement
from loops.interfaces import IConceptSchema, ILoopsAdapter
from loops.organize.interfaces import IPerson as IBasePerson
from loops.organize.interfaces import ITask as IBaseTask
from loops.schema.base import Relation, RelationSet
from loops.util import _


class IPerson(IBasePerson, IKnowing):
    """ A person, including knowledge/learning management features.
    """

    knowledge = RelationSet(
            title=_(u'Knowledge'),
            description=_(u'The knowledge elements for this person.'),
            #target_types=('topic',),   # set via global option knowledge.element
            required=False)


class ITask(IBaseTask, IRequirementProfile):
    """ A task, also acting as a knowledge requirement profile.
    """

    requirements = RelationSet(
            title=_(u'Requirements'),
            description=_(u'The knowledge required for this task.'),
            #target_types=('topic',),   # set via global option knowledge.element
            required=False)


class ITopic(IConceptSchema, IKnowledgeElement, ILoopsAdapter):
    """ Just a topic, some general classification concept.
    """

