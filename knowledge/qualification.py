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
        State('new', 'new', ('assign',), 
              color='grey'),
        State('open', 'open',
              ('register', 
                #'pass', 'fail', 
                'cancel', 'modify'),
              color='red'),
        State('registered', 'registered',
              ('register', 'pass', 'fail', 'unregister', 'cancel', 'modify'),
              color='yellow'),
        State('passed', 'passed',
              ('cancel', 'close', 'modify', 'open', 'expire'),
              color='green'),
        State('failed', 'failed',
              ('register', 'cancel', 'modify', 'open'),
              color='green'),
        State('expired', 'expired',
              ('register', 'cancel', 'modify', 'open'),
              color='red'),
        State('cancelled', 'cancelled', ('modify', 'open'),
              color='grey'),
        State('closed', 'closed', ('modify', 'open'),
              color='lightblue'),
        # not directly reachable states:
        State('open_x', 'open', ('modify',), color='red'),
        State('registered_x', 'registered', ('modify',), color='yellow'),
        # transitions:
        Transition('assign', 'assign', 'open'),
        Transition('register', 'register', 'registered'),
        Transition('pass', 'pass', 'passed'),
        Transition('fail', 'fail', 'failed'),
        Transition('unregister', 'unregister', 'open'),
        Transition('cancel', 'cancel', 'cancelled'),
        Transition('modify', 'modify', 'open'),
        Transition('close', 'close', 'closed'),
        Transition('open', 'open', 'open'),
        #initialState='open')
        initialState='new')  # TODO: handle assignment to competence


class QualificationRecord(WorkItem):

    implements(IQualificationRecord)

    typeName = 'QualificationRecord'
    typeInterface = IQualificationRecord
    statesDefinition = 'knowledge.qualification'

    def doAction(self, action, userName, **kw):
        new = self.createNew(action, userName, **kw)
        new.userName = self.userName
        new.doTransition(action)
        new.reindex()
        return new


class QualificationRecords(WorkItems):
    """ A tracking storage adapter managing qualification records.
    """

    implements(IQualificationRecords)
    adapts(ITrackingStorage)

