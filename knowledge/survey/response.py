#
#  Copyright (c) 2016 Helmut Merz helmutm@cy55.de
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
    personId = None
    institutionId = None
    referrerId = None

    def __init__(self, context):
        self.context = context

    def save(self, data):
        if self.personId:
            id = self.personId
            if self.institutionId:
                id += '.' + self.institutionId
            if self.referrerId:
                id += '.' + self.referrerId
            self.storage.saveUserTrack(self.uid, 0, id, data, 
                                        update=True, overwrite=False)

    def load(self, personId=None, referrerId=None, institutionId=None):
        if personId is None:
            personId = self.personId
        if referrerId is None:
            referrerId = self.referrerId
        if institutionId is None:
            institutionId = self.institutionId
        if personId:
            id = personId
            if institutionId:
                id += '.' + institutionId
            if referrerId:
                id += '.' + referrerId
            tracks = self.storage.getUserTracks(self.uid, 0, id)
            if not tracks:  # then try without institution
                tracks = self.storage.getUserTracks(self.uid, 0, personId)
            if tracks:
                return tracks[0].data
        return {}

    def loadRange(self, personId):
        tracks = self.storage.getUserTracks(self.uid, 0, personId)
        data = {}
        for tr in tracks:
            for k, v in tr.data.items():
                item = data.setdefault(k, [])
                item.append(v)
        return data

    def getAllTracks(self):
        return self.storage.query(taskId=self.uid)


class Response(Track):

    implements(IResponse)

    typeName = 'Response'

