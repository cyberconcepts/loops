# loops.organize.tracking.storage.compat

"""loops compatibility layer on cco.storage.tracking.

Provides a Container subclass that defines methods from cybertools...TrackingStorage
used by code based on loops.organize.tracking.
"""

from zope.interface import implementer
from cco.storage.tracking import record
from loops.util import IUid


@implementer(IUid)
class Track(record.Track):

    @property
    def taskId(self):
        return self.head.get('taskId')


class Container(record.Container):

    itemFactory = Track

    def saveUserTrack(self, taskId, runId, userName, data):
        track = self.itemFactory(taskId, userName, data=data)
        return self.save(track)

    def setTrackData(self, track, data):
        track.data = data
        self.update(track)

    def removeTrack(self, track):
        self.remove(track.trackId)

