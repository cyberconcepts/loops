#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
A framework for storing personal favorites and settings.
"""

from zope.component import adapts
from zope.interface import implements

from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrackingStorage
from loops.organize.personal.interfaces import IFavorites, IFavorite
from loops import util


class Favorites(object):

    implements(IFavorites)
    adapts(ITrackingStorage)

    def __init__(self, context):
        self.context = context

    def list(self, person, sortKey=None, type='favorite'):
        for item in self.listTracks(person, sortKey, type):
            yield item.taskId

    def listWithTracks(self, person, sortKey=None, type='favorite'):
        for item in self.listTracks(person, sortKey, type):
            yield util.getUidForObject(item), item.taskId

    def listTracks(self, person, sortKey=None, type='favorite'):
        if person is None:
            return
        personUid = util.getUidForObject(person)
        if sortKey is None:
            sortKey = lambda x: (x.data.get('order', 100), -x.timeStamp)
        for item in sorted(self.context.query(userName=personUid), key=sortKey):
            if type is not None:
                if item.type != type:
                    continue
            yield item

    def add(self, obj, person, data=None, nodups=True):
        if None in (obj, person):
            return False
        uid = util.getUidForObject(obj)
        personUid = util.getUidForObject(person)
        if data is None:
            data = {'type': 'favorite', 'order': 100}
        if nodups:
            for track in self.context.query(userName=personUid, taskId=uid):
                if track.type == data['type']:    # already present
                    return False
        return self.context.saveUserTrack(uid, 0, personUid, data)

    def remove(self, obj, person, type='favorite'):
        if None in (obj, person):
            return False
        uid = util.getUidForObject(obj)
        personUid = util.getUidForObject(person)
        changed = False
        for track in self.context.query(userName=personUid, taskId=uid):
            if track.type == type:
                changed = True
                self.context.removeTrack(track)
        return changed

    def reorder(self, uids):
        offset = 0
        for idx, uid in enumerate(uids):
            track = util.getObjectForUid(uid)
            if track is not None:
                data = track.data
                order = data.get('order', 100)
                if order < idx or (order >= 100 and order < idx + 100):
                    offset = 100
                data['order'] = idx + offset
                track.data = data


class Favorite(Track):

    implements(IFavorite)

    typeName = 'Favorite'

    @property
    def type(self):
        return self.data.get('type') or 'favorite'


def updateSortInfo(person, task, data):
    if person is not None:
        favorites = task.getLoopsRoot().getRecordManager().get('favorites')
        if favorites is None:
            return data
        personUid = util.getUidForObject(person)
        taskUid = util.getUidForObject(task)
        for fav in favorites.query(userName=personUid, taskId=taskUid):
            if fav.data.get('type') == 'sort':
                fdata = fav.data['sortInfo']
                if not data:
                    data = fdata
                else:
                    if data != fdata:
                        newData = fav.data
                        newData['sortInfo'] = data
                        fav.data = newData
                break
        else:
            if data:
                Favorites(favorites).add(task, person,
                                         dict(type='sort', sortInfo=data))
    return data


def setInstitution(person, inst):
    if person is not None:
        favorites = inst.getLoopsRoot().getRecordManager().get('favorites')
        if favorites is None:
            return
        personUid = util.getUidForObject(person)
        taskUid = util.getUidForObject(inst)
        for fav in favorites.query(userName=personUid):
            if fav.type == 'institution':
                fav.taskId = taskUid
                favorites.indexTrack(None, fav, 'taskId')
        else:
            Favorites(favorites).add(inst, person, dict(type='institution'))
