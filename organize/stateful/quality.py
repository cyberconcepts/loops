#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope import component
from zope.component import adapter
from zope.interface import implementer
from zope.traversing.api import getName

from cybertools.stateful.definition import registerStatesDefinition
from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition, IStateful
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.interfaces import ILoopsObject, IResource
from loops.organize.stateful.base import StatefulLoopsObject


@implementer(IStatesDefinition)
def classificationQuality():
    return StatesDefinition('classificationQuality',
        State('new', 'new', ('classify', 'verify',
                             'change_classification', 'remove_classification'),
              color='red'),
        State('unclassified', 'unclassified', ('classify', 'verify'),
              color='red'),
        State('classified', 'classified',
              ('verify', 'change_classification', 'remove_classification'),
              color='yellow'),
        State('verified', 'verified',
              ('change_classification', 'remove_classification'),
              color='green'),
        Transition('classify', 'classify', 'classified'),
        Transition('verify', 'verify', 'verified'),
        Transition('change_classification', 'change classification', 'classified'),
        Transition('remove_classification', 'remove classification', 'unclassified'),
        initialState='new')


class ClassificationQualityCheckable(StatefulLoopsObject):

    statesDefinition = 'loops.classification_quality'

    def getAvailableTransitionsForUser(self):
        return [tr for tr in self.getAvailableTransitions()
                   if tr.name == 'verify']

    # automatic transitions

    def assign(self, relation):
        if not self.isRelevant(relation):
            return
        if self.state in ('new', 'unclassified'):
            self.doTransition('classify')
        else:
            self.doTransition('change_classification')

    def deassign(self, relation):
        if not self.isRelevant(relation):
            return
        if self.state in ('new', 'classified', 'verified'):
            old = self.context.getParentRelations()
            if len(old) > 2:    # the hasType relation always remains
                self.doTransition('change_classification')
            else:
                self.doTransition('remove_classification')

    def isRelevant(self, relation):
        """ Return True if the relation given is relevant for changing
            the quality state.
        """
        return (IResource.providedBy(self.context) and
                getName(relation.predicate) != 'hasType')


# event handlers

@adapter(ILoopsObject, IAssignmentEvent)
def assign(obj, event):
    stf = component.getAdapter(event.relation.second, IStateful,
                               name='loops.classification_quality')
    stf.assign(event.relation)

@adapter(ILoopsObject, IDeassignmentEvent)
def deassign(obj, event):
    stf = component.getAdapter(event.relation.second, IStateful,
                               name='loops.classification_quality')
    stf.deassign(event.relation)
