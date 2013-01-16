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
Basic implementations for stateful objects and adapters.
"""

from zope.app.security.settings import Allow, Deny, Unset
from zope import component
from zope.component import adapter
from zope.interface import implementer
from zope.traversing.api import getName

from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition, IStateful
from loops.common import adapted
from loops.organize.stateful.base import StatefulLoopsObject
from loops.security.interfaces import ISecuritySetter


def setPermissionsForRoles(settings):
    def setSecurity(obj):
        setter = ISecuritySetter(obj.context)
        setter.setRolePermissions(settings)
        setter.propagateSecurity()
    return setSecurity


@implementer(IStatesDefinition)
def taskStates():
    return StatesDefinition('task_states',
        State('draft', 'draft', ('release', 'cancel',),
              color='blue'),
        State('active', 'active', ('finish', 'cancel',),
              color='yellow'),
        State('finished', 'finished', ('reopen', 'archive',),
              color='green'),
        State('cancelled', 'cancelled', ('reopen',),
              color='x'),
        State('archived', 'archived', ('reopen',),
              color='grey'),
        Transition('release', 'release', 'active'),
        Transition('finish', 'finish', 'finished'),
        Transition('cancel', 'cancel', 'cancelled'),
        Transition('reopen', 're-open', 'draft'),
        initialState='draft')


@implementer(IStatesDefinition)
def publishableTask():
    return StatesDefinition('publishable_task',
        State('draft', 'draft', ('release', 'release_publish', 'cancel',),
              color='yellow',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Deny,
                  ('zope.View', 'loops.Member'): Deny,
                  ('zope.View', 'loops.Person'): Deny,
                  ('zope.View', 'loops.Staff'): Deny,})),
        State('active', 'active', ('retract', 'finish', 'publish', 'cancel',),
              color='lightblue',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Deny,
                  ('zope.View', 'loops.Member'): Deny,
                  ('zope.View', 'loops.Person'): Allow,
                  ('zope.View', 'loops.Staff'): Deny,})),
        State('active_published', 'active (published)', 
              ('retract', 'finish_published', 'retract', 'cancel',), color='blue',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Allow,
                  ('zope.View', 'loops.Member'): Allow,
                  ('zope.View', 'loops.Person'): Allow,
                  ('zope.View', 'loops.Staff'): Allow,})),
        State('finished', 'finished', ('reopen', 'archive',),
              color='lightgreen',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Deny,
                  ('zope.View', 'loops.Member'): Deny,
                  ('zope.View', 'loops.Person'): Allow,
                  ('zope.View', 'loops.Staff'): Deny,})),
        State('finished_published', 'finished (published)', ('reopen', 'archive',),
              color='green',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Allow,
                  ('zope.View', 'loops.Member'): Allow,
                  ('zope.View', 'loops.Person'): Allow,
                  ('zope.View', 'loops.Staff'): Allow,})),
        State('cancelled', 'cancelled', ('reopen',),
              color='x',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Deny,
                  ('zope.View', 'loops.Member'): Deny,
                  ('zope.View', 'loops.Person'): Deny,
                  ('zope.View', 'loops.Staff'): Deny,})),
        State('archived', 'archived', ('reopen',),
              color='grey',
              setSecurity=setPermissionsForRoles({
                  ('zope.View', 'zope.Member'): Deny,
                  ('zope.View', 'loops.Member'): Deny,
                  ('zope.View', 'loops.Person'): Deny,
                  ('zope.View', 'loops.Staff'): Deny,})),
        Transition('release', 'release', 'active'),
        Transition('release_publish', 'release, publish', 'active_published'),
        Transition('publish', 'publish', 'active_published'),
        Transition('retract', 'retract', 'draft'),
        Transition('finish', 'finish', 'finished'),
        Transition('finish_published', 'finish (published)', 'finished_published'),
        Transition('cancel', 'cancel', 'cancelled'),
        Transition('reopen', 're-open', 'draft'),
        Transition('archive', 'archive', 'archived'),
        initialState='draft')


class StatefulTask(StatefulLoopsObject):

    statesDefinition = 'task_states'


class PublishableTask(StatefulLoopsObject):

    statesDefinition = 'publishable_task'

