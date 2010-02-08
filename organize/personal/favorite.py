#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Base classes for a notification framework.

$Id$
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

    def list(self, person, sortKey=None):
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

    def remove(self, obj, person):
        if None in (obj, person):
            return False
        uid = util.getUidForObject(obj)
        personUid = util.getUidForObject(person)
        changed = False
        for t in self.context.query(userName=personUid, taskId=uid):
            changed = True
            self.context.removeTrack(t)
        return changed


class Favorite(Track):

    implements(IFavorite)

    typeName = 'Favorite'

