# loops.storage.compat.tracking

"""loops compatibility layer on scopes.storage.tracking.

Provides a Container subclass that defines methods from cybertools...TrackingStorage
used by code based on loops.organize.tracking.
"""

from zope.interface import implementer

from scopes.storage import tracking
from loops.util import IUid


@implementer(IUid)
class Track(tracking.Track):

    pass


class Container(tracking.Container):

    itemFactory = Track

    def saveUserTrack(self, taskId, runId, userName, data):
        track = self.itemFactory(taskId, userName, data=data)
        return self.save(track)

    def setTrackData(self, track, data):
        track.data = data
        self.update(track)

    def removeTrack(self, track):
        self.remove(track.trackId)

