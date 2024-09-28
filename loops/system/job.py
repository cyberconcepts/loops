# loops.system.job

""" Recording changes to loops objects.
"""

from zope.interface import implementer
from zope.cachedescriptors.property import Lazy
from zope.component import adapter

from cybertools.meta.interfaces import IOptions
from cybertools.tracking.btree import Track, getTimeStamp
from loops.organize.tracking.base import BaseRecordManager
from loops.system.interfaces import IJobRecord, IJobRecords
from loops import util


@implementer(IJobRecords)
class JobRecords(BaseRecordManager):

    storageName = 'jobs'

    def __init__(self, context):
        self.context = context

    def recordExecution(self, job, state, transcript, **kw):
        taskId = util.getUidForObject(job)
        kw['state'] = state
        kw['transcript'] = transcript
        self.storage.saveUserTrack(taskId, 0, self.personId, kw)

    def getLastRecordFor(self, job):
        taskId = util.getUidForObject(job)
        recs = self.storage.query(taskId=taskId)
        if recs:
            return sorted(recs, key=lambda x: x.timeStamp)[-1]
        return None


@implementer(IJobRecord)
class JobRecord(Track):

    typeName = 'JobRecord'

