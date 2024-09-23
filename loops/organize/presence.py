#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Utility for collecting information about logged-in/active users.

Author: Hannes Plattner.

$Id$
"""

from zope.interface import implements
from zope.cachedescriptors.property import Lazy

from cybertools.meta.interfaces import IOptions
from cybertools.util.date import getTimeStamp
from loops.organize.interfaces import IPresence
from loops.organize.party import getPersonForUser
from loops.organize import util


class Presence(object):

    implements(IPresence)

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
