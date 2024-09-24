# loops.organize.tracking.access

""" Recording changes to loops objects.
"""

import logging
import os
import time

import transaction
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapter
from zope.interface import Interface, implementer
from zope.security.proxy import removeSecurityProxy
from zope.session.interfaces import ISession

from cybertools.browser.view import IBodyRenderedEvent
from cybertools.meta.interfaces import IOptions
from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrack
from cybertools.tracking.logfile import Logger, loggers
from cybertools.util.date import getTimeStamp
from loops.interfaces import ILoopsObject
from loops.organize.job.base import JobManager
from loops.organize.tracking.base import BaseRecordManager
from loops import util


packageId = 'loops.organize.tracking.access'

# logging

logfile_option = 'organize.tracking.logfile'
request_key = 'loops.organize.tracking.access'

fields = {
    '001': ('principal', 'node', 'target', 'view', 'params'),
}

version = '001'

accessTrailSize = 50


def record(request, **kw):
    data = request.annotations.setdefault(request_key, {})
    for k, v in kw.items():
        data[k] = v



@adapter(IBodyRenderedEvent)
def logAccess(event, baseDir=None):
    context = event.context
    if not ILoopsObject.providedBy(context):
        return
    data = event.request.annotations.get(request_key)
    if not data:
        return
    context = removeSecurityProxy(context)
    if 'principal' in data:
        storeAccessTrail(context, event.request, data)
    options = IOptions(context.getLoopsRoot())
    logfileOption = options(logfile_option)
    if not logfileOption:
        return
    fn = logfileOption[0]
    logger = loggers.get(fn)
    if not logger:
        path = os.path.join(baseDir or util.getVarDirectory(), fn)
        logger = loggers[fn] = Logger(fn, path)
    logger.log(marshall(data))

def storeAccessTrail(context, request, data):
    """ Keep records in Session for access history"""
    session = ISession(request)[packageId]
    item = session.setdefault('accessTrail', [])[:accessTrailSize]
    record = dict((key, data.get(key) or '') for key in fields[version])
    record['timeStamp'] = getTimeStamp()
    record['version'] = version
    item.insert(0, record)
    session['accessTrail'] = item

def marshall(data):
    values = [version]
    for key in fields[version]:
        values.append(data.get(key) or '')
    return ';'.join(values)


# record manager

class AccessRecordManager(BaseRecordManager, JobManager):

    storageName = 'access'

    def __init__(self, context):
        self.context = context
        self.baseDir = util.getVarDirectory()

    def process(self):
        return self.loadRecordsFromLog()

    @Lazy
    def logfile(self):
        value = self.options(logfile_option)
        return value and value[0] or None

    @Lazy
    def valid(self):
        return self.storage is not None and self.logfile

    @Lazy
    def log(self):
        return logging.getLogger('AccessRecordManager')

    def loadRecordsFromLog(self):
        if not self.valid:
            return 'AccessRecordManager: Feature not available.'
        count = 0
        fn = self.logfile
        path = os.path.join(self.baseDir, fn)
        logger = loggers.get(fn)
        if not logger:
            logger = loggers[fn] = Logger(fn, path)
        if not os.path.exists(path):
            return
        lf = open(path, 'r')
        for idx, line in enumerate(lf):
            if self.processLogRecord(idx, line):
                count += 1
        lf.close()
        transaction.commit()
        logger.doRollover()
        self.log.info('%i records loaded.' % count)
        return 'AccessRecordManager: %i records loaded.' % count

    def processLogRecord(self, idx, line):
        if not line:
            return False
        values = line.split(';')
        timeString = values.pop(0)
        version = values.pop(0)
        if version not in fields:
            self.log.warn('Undefined logging record version %r on record %i.'
                                    % (version, idx))
            return False
        if len(values) != len(fields[version]):
            self.log.warn('Length of record %i does not match version %r.'
                                    % (idx, version))
            return False
        data = {}
        for idx, field in enumerate(fields[version]):
            data[field] = values[idx]
        timeStamp = timeStringToTimeStamp(timeString)
        personId = self.getPersonId(data['principal'])
        taskId = data['target'] or data['node']
        existing = self.storage.query(taskId=taskId, userName=self.personId,
                                      timeStamp=timeStamp)
        for track in existing:
            if track.data == data:  # has been recorded already
                return False
        self.storage.saveUserTrack(taskId, 0, personId, data,
                                   timeStamp=timeStamp)
        return True


class AccessRecordManagerView(AccessRecordManager):
    # obsolete, records are now loaded via AccessRecordManager adapter
    # that is called via a job executor view.

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.baseDir = util.getVarDirectory()


class IAccessRecord(ITrack):

    pass


@implementer(IAccessRecord)
class AccessRecord(Track):

    typeName = 'AccessRecord'


def timeStringToTimeStamp(timeString):
    s, decimal = timeString.split(',')
    t = time.strptime(s, '%Y-%m-%d %H:%M:%S')
    return int(time.mktime(t))
