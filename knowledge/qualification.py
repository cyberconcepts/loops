#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Controlling qualification activities of persons.

Central part of CCM competence and certification management framework.
"""

from zope.component import adapts
from zope.interface import implementer, implements

from cybertools.stateful.base import Stateful
from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition
from cybertools.tracking.interfaces import ITrackingStorage
from loops.knowledge.interfaces import IQualificationRecord, \
            IQualificationRecords
from loops.organize.work.base import WorkItem, WorkItems


@implementer(IStatesDefinition)
def qualificationStates():
    return StatesDefinition('qualification',
        State('new', 'new',
              ('plan', 'accept', 'start', 'work', 'finish', 'delegate', 'cancel'),
              color='red'),)


class QualificationRecord(WorkItem):

    implements(IQualificationRecord)

    typeName = 'QualificationRecord'
    statesDefinition = 'knowledge.qualification'


class QualificationRecords(WorkItems):
    """ A tracking storage adapter managing qualification records.
    """

    implements(IQualificationRecords)
    adapts(ITrackingStorage)

