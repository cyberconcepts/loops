#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
Implementations for stateful persons.
"""

from zope.app.security.settings import Allow, Deny, Unset
from zope import component
from zope.component import adapter
from zope.interface import implementer
from zope.traversing.api import getName

from cybertools.composer.schema.schema import Schema
from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition, IStateful
from loops.common import adapted
from loops.organize.stateful.base import commentsField
from loops.organize.stateful.base import StatefulLoopsObject
from loops.security.interfaces import ISecuritySetter
from loops.util import _


defaultSchema = Schema(commentsField, 
                       name='change_state')


@implementer(IStatesDefinition)
def personStates():
    return StatesDefinition('person_states',
        State('prospective', 'prospective', ('activate', 'inactivate',),
              color='blue'),
        State('active', 'active', ('reset', 'inactivate',),
              color='green'),
        State('inactive', 'inactive', ('reactivate',),
              color='x'),
        Transition('activate', 'activate', 'active', schema=defaultSchema),
        Transition('reset', 'reset', 'prospective', schema=defaultSchema),
        Transition('inactivate', 'inactivate', 'inactive', schema=defaultSchema),
        Transition('reactivate', 'reactivate', 'active', schema=defaultSchema),
        initialState='active')


class StatefulPerson(StatefulLoopsObject):

    statesDefinition = 'person_states'

