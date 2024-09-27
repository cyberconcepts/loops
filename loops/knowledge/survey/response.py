# loops.knowledge.survey.response

""" Handling survey responses.
"""

from zope.component import adapts
from zope.interface import implementer

from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrackingStorage
from loops.knowledge.survey.interfaces import IResponse, IResponses
from loops.organize.tracking.base import BaseRecordManager


@implementer(IResponses)
class Responses(BaseRecordManager):

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


@implementer(IResponse)
class Response(Track):

    typeName = 'Response'

