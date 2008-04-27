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

from zope.app.catalog.interfaces import ICatalog
from zope import component
from zope.component import adapts, adapter

from cybertools.meta.interfaces import IOptions
from cybertools.stateful.base import Stateful as BaseStateful
from cybertools.stateful.base import StatefulAdapter, IndexInfo
from cybertools.stateful.interfaces import IStatesDefinition, ITransitionEvent
from loops.interfaces import ILoopsObject, IResource
from loops import util


class Stateful(BaseStateful):

    def getStatesDefinition(self):
        return component.getUtility(IStatesDefinition, self.statesDefinition)


class StatefulLoopsObject(Stateful, StatefulAdapter):

    adapts(ILoopsObject)


class SimplePublishable(StatefulLoopsObject):

    statesDefinition = 'loops.simple_publishing'


class StatefulResourceIndexInfo(IndexInfo):

    adapts(IResource)

    @property
    def availableStatesDefinitions(self):
        options = IOptions(self.context.getLoopsRoot())
        return options('organize.stateful.resource', ())


@adapter(IResource, ITransitionEvent)
def handleTransition(self, obj, event):
    previous = event.previousState
    next = event.transition.targetState
    if next != previous:
        cat = getUtility(ICatalog)
        cat.index_doc(int(util.getUidForObject(obj)), obj)
