#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Provide member properties based on person data.

$Id$
"""

from zope import component
from zope.app.security.interfaces import IAuthentication
from zope.cachedescriptors.property import Lazy

from cybertools.browser.member import MemberInfoProvider as BaseMemberInfoProvider
from cybertools.browser.member import MemberProperty
from cybertools.util.jeep import Jeep
from loops.common import adapted
from loops.organize.party import getPersonForUser
from loops import util


class MemberInfoProvider(BaseMemberInfoProvider):

    def getData(self, principalId=None):
        if principalId is None:
            principal = self.request.principal
        else:
            #auth = component.getUtility(IAuthentication, self.context)
            auth = component.getUtility(IAuthentication)
            principal = auth.getPrincipal(principalId)
        person = getPersonForUser(self.context, self.request, principal)
        if person is None:
            return super(MemberInfoProvider, self).getData(principalId)
        aPerson = adapted(person)
        return Jeep((MemberProperty('id', principal.id, u'ID'),
                     MemberProperty('title', aPerson.title, u'Title'),
                     MemberProperty('description', aPerson.description,
                                    u'Description'),
                     MemberProperty('object', person, u'Object'),
                     MemberProperty('adapted', aPerson, u'Adapted object'),
                   ))

