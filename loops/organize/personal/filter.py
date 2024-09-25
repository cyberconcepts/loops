# loops.organize.personal.filter

""" Base classes for filters.
"""

from zope.component import adapts
from zope.interface import implementer

from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrackingStorage
from loops.organize.personal.interfaces import IFilters, IFilter
from loops import util


@implementer(IFilters)
class Filters(object):

    adapts(ITrackingStorage)

    def __init__(self, context):
        self.context = context

    def list(self, person, activeOnly=True, sortKey=None):
        for item in self.listTracks(person, sortKey):
            yield item.taskId

    def listTracks(self, person, sortKey=None):
        if person is None:
            return
        personUid = util.getUidForObject(person)
        if sortKey is None:
            sortKey = lambda x: -x.timeStamp
        for item in sorted(self.context.query(userName=personUid), key=sortKey):
            yield item

    def add(self, obj, person, data=None):
        if None in (obj, person):
            return False
        uid = util.getUidForObject(obj)
        personUid = util.getUidForObject(person)
        if self.context.query(userName=personUid, taskId=uid):
            return False
        if data is None:
            data = {}
        return self.context.saveUserTrack(uid, 0, personUid, data)

    def remove(self, uid, person):
        changed = False
        personUid = util.getUidForObject(person)
        for t in self.context.query(userName=personUid, taskId=uid):
            changed = True
            self.context.removeTrack(t)
        return changed


@implementer(IFilter)
class Filter(Track):

    typeName = 'Filter'

