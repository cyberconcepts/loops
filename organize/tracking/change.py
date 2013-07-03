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
Recording changes to loops objects.

$Id$
"""

from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent
from zope.app.container.interfaces import IObjectMovedEvent
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectModifiedEvent, IObjectCreatedEvent

from cybertools.meta.interfaces import IOptions
from cybertools.tracking.btree import Track, getTimeStamp
from cybertools.tracking.interfaces import ITrack
from loops.concept import ConceptManager
from loops.resource import ResourceManager
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.interfaces import ILoopsObject
from loops.organize.party import getPersonForUser
from loops.organize.tracking.base import BaseRecordManager
from loops.security.common import getCurrentPrincipal
from loops import util


class ChangeManager(BaseRecordManager):

    storageName = 'changes'

    def __init__(self, context):
        if isinstance(context, (ConceptManager, ResourceManager)):
            return
        self.context = context

    @Lazy
    def valid(self):
        return (not (self.context is None or
                    self.storage is None or
                    self.personId is None)
                and self.options('organize.tracking.changes'))

    def recordModification(self, action='modify', **kw):
        if not self.valid:
            return
        uid = util.getUidForObject(self.context)
        last = self.storage.getLastUserTrack(uid, 0, self.personId)
        update = (last is not None and last.data.get('action') == action and
                  last.metadata['timeStamp'] >= getTimeStamp() - 5)
        data = dict(action=action)
        relation = kw.get('relation')
        if relation is not None:
            data['predicate'] = util.getUidForObject(relation.predicate)
            data['second'] = util.getUidForObject(relation.second)
        event = kw.get('event')
        if event is not None:
            desc = getattr(event, 'descriptions', ())
            for item in desc:
                if isinstance(item, dict):
                    data.update(item)
        if update:
            self.storage.updateTrack(last, data)
        else:
            self.storage.saveUserTrack(uid, 0, self.personId, data, update)


class IChangeRecord(ITrack):

    pass


class ChangeRecord(Track):

    implements(IChangeRecord)

    typeName = 'ChangeRecord'


@adapter(ILoopsObject, IObjectModifiedEvent)
def recordModification(obj, event):
    ChangeManager(obj).recordModification(event=event)

@adapter(ILoopsObject, IObjectAddedEvent)
def recordAdding(obj, event):
    ChangeManager(obj).recordModification('add', event=event)

@adapter(ILoopsObject, IAssignmentEvent)
def recordAssignment(obj, event):
    ChangeManager(obj).recordModification('assign', 
                            event=event, relation=event.relation)

@adapter(ILoopsObject, IDeassignmentEvent)
def recordDeassignment(obj, event):
    ChangeManager(obj).recordModification('deassign', 
                            event=event, relation=event.relation)
