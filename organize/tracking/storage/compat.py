# loops.organize.tracking.storage.compat

"""loops compatibility layer on cco.storage.tracking.

Provides a Container subclass that defines methods from cybertools...TrackingStorage
used by code based on loops.organize.tracking.
"""

from cco.storage.tracking import record


class Track(record.Track):

    @property
    def taskId(self):
        return self.head.get('taskId')


class Container(record.Container):

    itemFactory = Track

    def saveUserTrack(self, taskId, runId, userName, data):
        track = self.itemFactory(taskId, userName, data=data)
        return self.save(track)
