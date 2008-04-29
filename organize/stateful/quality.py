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
from loops.versioning.interfaces import IVersionable


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
        versionable = IVersionable(self.context, None)
        if self.state in ('new', 'unclassified'):
            self.doTransitionWithVersions('classify', versionable)
        else:
            self.doTransitionWithVersions('change_classification', versionable)

    def deassign(self, relation):
        if not self.isRelevant(relation):
            return
        versionable = IVersionable(self.context, None)
        if self.state in ('new', 'classified', 'verified'):
            parents = [r for r in self.context.getParentRelations()
                         if r.predicate != self.typePredicate]
            if len(parents) > 0:
                self.doTransitionWithVersions('change_classification', versionable)
            else:
                self.doTransitionWithVersions('remove_classification', versionable)

    def doTransitionWithVersions(self, transition, versionable):
        self.doTransition(transition)
        if versionable is None:
            return
        for v in versionable.versions.values():
            if v != self.context:
                stf = component.getAdapter(v, IStateful, name=self.statesDefinition)
                available = [t.name for t in stf.getAvailableTransitions()]
                if transition in available:
                    stf.doTransition(transition)
                #else:
                #    print '***', v.__name__, stf.state, transition, available

    def isRelevant(self, relation):
        """ Return True if the relation given is relevant for changing
            the quality state.
        """
        return (IResource.providedBy(self.context) and
                getName(relation.predicate) != 'hasType')

    def getState(self):
        value = super(ClassificationQualityCheckable, self).getState()
        if value == 'new':
            parents = [r for r in self.context.getParentRelations()
                         if r.predicate != self.typePredicate]
            if len(parents) > 0:
                value = 'classified'
        return value
    def setState(self, value):
        super(ClassificationQualityCheckable, self).setState(value)
    state = property(getState, setState)


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
