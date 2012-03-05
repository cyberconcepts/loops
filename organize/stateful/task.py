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
Basic implementations for stateful objects and adapters.
"""

from zope import component
from zope.component import adapter
from zope.interface import implementer
from zope.traversing.api import getName

from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition, IStateful
from loops.common import adapted
from loops.organize.stateful.base import StatefulLoopsObject


@implementer(IStatesDefinition)
def taskStates():
    return StatesDefinition('task_states',
        State('planned', 'planned', ('finish', 'cancel'),
              color='yellow'),
        State('finished', 'finished', ('reopen'),
              color='green'),
        State('cancelled', 'cancelled', ('reopen'),
              color='grey'),
        Transition('finish', 'finish', 'finished'),
        Transition('cancel', 'cancel', 'cancelled'),
        Transition('reopen', 're-open', 'planned'),
        initialState='planned')


class StatefulTask(StatefulLoopsObject):

    statesDefinition = 'task_states'

