#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
Handling survey responses.
"""

from zope.component import adapts
from zope.interface import implements

from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrackingStorage
from loops.knowledge.survey.interfaces import IResponse, IResponses
from loops.organize.tracking.base import BaseRecordManager


class Responses(BaseRecordManager):

    implements(IResponses)

    storageName = 'survey_responses'

    def __init__(self, context):
        self.context = context

    def save(self, data):
        if not self.personId:
            return
        tracks = self.storage.getUserTracks(self.uid, 0, self.personId)
        if tracks:
            self.storage.updateTrack(tracks[0], data)
        else:
            self.storage.saveUserTrack(self.uid, 0, self.personId, data)

    def load(self):
        if self.personId:
            tracks = self.storage.getUserTracks(self.uid, 0, self.personId)
            if tracks:
                return tracks[0].data
        return {}


class Response(Track):

    implements(IResponse)

    typeName = 'Response'

