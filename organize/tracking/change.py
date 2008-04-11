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
from zope.cachedescriptors.property import Lazy
from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectModifiedEvent, IObjectCreatedEvent

from cybertools.tracking.btree import Track, getTimeStamp
from loops.concept import ConceptManager
from loops.resource import ResourceManager
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.interfaces import ILoopsObject
from loops.organize.party import getPersonForUser
from loops.security.common import getCurrentPrincipal
from loops import util


class ChangeManager(object):

    context = None

    def __init__(self, context):
        if isinstance(context, (ConceptManager, ResourceManager)):
            return
        self.context = context

    @Lazy
    def options(self):
        return IOptions(self.context)

    @Lazy
    def valid(self):
        return not (self.context is None or
                    self.storage is None or
                    self.person is None)
        # and 'changes' in self.options.tracking

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def storage(self):
        records = self.loopsRoot.getRecordManager()
        if records is not None:
            return records.get('changes')
        return None

    @Lazy
    def person(self):
        principal = getCurrentPrincipal()
        if principal is not None:
            return getPersonForUser(self.context, principal=principal)
        return None

    def recordModification(self, event=None):
        if not self.valid:
            return
        uid = util.getUidForObject(self.context)
        personUid = util.getUidForObject(self.person)
        last = self.storage.getLastUserTrack(uid, 0, personUid)
        if last is None or last.metadata['timeStamp'] < getTimeStamp() - 5:
            self.storage.saveUserTrack(uid, 0, personUid, dict(action='modify'))


class ChangeRecord(Track):

    typeName = 'ChangeRecord'


@adapter(ILoopsObject, IObjectModifiedEvent)
def recordModification(obj, event):
    ChangeManager(obj).recordModification(event)
