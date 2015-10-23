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
Storing and retrieving notifications.
"""

from cybertools.util.date import getTimeStamp
from loops.common import baseObject
from loops.organize.personal.favorite import Favorites
from loops import util


class Notifications(Favorites):

    def __init__(self, person):
        self.person = person
        self.context = (baseObject(person).
                            getLoopsRoot().getRecordManager()['favorites'])

    def listTracks(self):
        return super(Notifications, self).listTracks(
                        baseObject(self.person), type='notification')

    def add(self, obj, sender, text):
        senderUid = util.getUidForObject(baseObject(sender))
        super(Notifications, self).add(baseObject(obj), baseObject(self.person), 
                dict(type='notification', sender=senderUid, text=text),
                nodups=False)

    def read(self, track):
        data = track.data
        data['read_ts'] = getTimeStamp()
        track.data = data

    def unread(self, track):
        data = track.data
        data['read_ts'] = None
        track.data = data

    def remove(self, track):
        self.context.removeTrack(track)
