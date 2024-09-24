# loops.organize.memberinfo

""" Provide member properties based on person data.
"""

from zope import component
from zope.authentication.interfaces import IAuthentication
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

