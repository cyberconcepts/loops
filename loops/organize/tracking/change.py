# loops.organize.tracking.change

""" Recording changes to loops objects.
"""

from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent
from zope.app.container.interfaces import IObjectMovedEvent
from zope.interface import implementer
from zope.cachedescriptors.property import Lazy
from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectModifiedEvent, IObjectCreatedEvent
from zope.traversing.api import getName

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
        return self.isValid()

    def isValid(self, data={}, **kw):
        req = util.getRequest()
        if req and req.form.get('organize.suppress_tracking'):
            return False
        if self.context is None or self.storage is None or self.personId is None:
            return False
        if kw.get('force') or data.get('transition'):
            return True
        opt = self.options('organize.tracking.changes')
        if isinstance(opt, (list, tuple)):
            if hasattr(self.context, 'getType'):
                type = self.context.getType()
                return type and getName(type) in opt
            return False
        else:
            return bool(opt)

    def recordModification(self, action='modify', **kw):
        data = dict(action=action)
        event = kw.get('event')
        if event is not None:
            desc = getattr(event, 'descriptions', ())
            for item in desc:
                if isinstance(item, dict):
                    data.update(item)
        if not self.isValid(data, **kw):
            return
        uid = util.getUidForObject(self.context)
        last = self.storage.getLastUserTrack(uid, 0, self.personId)
        update = (last is not None and last.data.get('action') == action and
                  last.metadata['timeStamp'] >= getTimeStamp() - 5)
        relation = kw.get('relation')
        if relation is not None:
            data['predicate'] = util.getUidForObject(relation.predicate)
            data['second'] = util.getUidForObject(relation.second)
        if update:
            self.storage.updateTrack(last, data)
        else:
            self.storage.saveUserTrack(uid, 0, self.personId, data, update)


class IChangeRecord(ITrack):

    pass


@implementer(IChangeRecord)
class ChangeRecord(Track):

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
