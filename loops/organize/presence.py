# loops.organize.presence

""" Utility for collecting information about logged-in/active users.

Author: Hannes Plattner.
"""

from zope.interface import implementer
from zope.cachedescriptors.property import Lazy

from cybertools.meta.interfaces import IOptions
from cybertools.util.date import getTimeStamp
from loops.organize.interfaces import IPresence
from loops.organize.party import getPersonForUser
from loops.organize import util


@implementer(IPresence)
class Presence(object):

    def __init__(self, min_until_logout=10, presentUsers=None):
        self.min_until_logout = min_until_logout
        self.presentUsers = presentUsers or {}

    def update(self, principalId):
        self.addPresentUser(principalId)
        self.removeInactiveUsers()

    def addPresentUser(self, principalId):
        self.presentUsers[principalId] = getTimeStamp()

    def removeInactiveUsers(self):
        toDelete = []
        for id, timeStamp in self.presentUsers.iteritems():
            if (getTimeStamp() - timeStamp) > (self.min_until_logout*60):
                toDelete.append(id)
        for id in toDelete:
            if id in self.presentUsers:
                del self.presentUsers[id]

    def getPresentUsers(self, context=None):
        ret = []
        for id, timeStamp in self.presentUsers.iteritems():
            principal = util.getPrincipalForUserId(id)
            person = getPersonForUser(context, principal=principal)
            ret.append(person or principal)
        return ret

    def removePresentUser(self, principalId):
        if principalId in self.presentUsers:
            del self.presentUsers[principalId]
