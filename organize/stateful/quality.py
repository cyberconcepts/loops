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
        State('unclassified', 'unclassified', ('classify',)),
        State('classified', 'classified',
              ('verify', 'change_classification', 'remove_classification')),
        State('verified', 'verified',
              ('change_classification', 'remove_classification')),
        Transition('classify', 'classify', 'classified'),
        Transition('verify', 'verify', 'verified'),
        Transition('change_classification', 'change classification', 'classified'),
        Transition('remove_classification', 'remove classification', 'unclassified'),
        initialState='unclassified')


class ClassificationQualityCheckable(StatefulLoopsObject):

    statesDefinition = 'loops.classification_quality'


# event handlers

@adapter(ILoopsObject, IAssignmentEvent)
def assign(obj, event):
    target = event.relation.second
    if not IResource.providedBy(target):
        return
    pred = event.relation.predicate
    if getName(pred) == 'hasType':
        return
    stf = component.getAdapter(target, IStateful, name='loops.classification_quality')
    if stf.state == 'unclassified':
        stf.doTransition('classify')
    else:
        stf.doTransition('change_classification')

@adapter(ILoopsObject, IDeassignmentEvent)
def deassign(obj, event):
    target = event.relation.second
    if not IResource.providedBy(target):
        return
    pred = event.relation.predicate
    if getName(pred) == 'hasType':
        return
    stf = component.getAdapter(target, IStateful, name='loops.classification_quality')
    if stf.state in ('classified', 'verified'):
        old = target.getParentRelations()
        if len(old) > 2:    # the hasType relation always remains
            stf.doTransition('change_classification')
        else:
            stf.doTransition('remove_classification')
