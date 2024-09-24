# loops.organize.tracking.base

""" Base class(es) for track/record managers.
"""

from zope.authentication.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy

from cybertools.meta.interfaces import IOptions
from loops.organize.party import getPersonForUser
from loops.organize.util import getPrincipalForUserId
from loops.security.common import getCurrentPrincipal
from loops import util


class BaseRecordManager(object):

    context = None
    valid = True
    storageName = None

    @Lazy
    def options(self):
        #return IOptions(self.context)
        return IOptions(self.loopsRoot)

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def uid(self):
        return util.getUidForObject(self.context)

    @Lazy
    def storage(self):
        records = self.loopsRoot.getRecordManager()
        if records is not None:
            return records.get(self.storageName)
        return None

    @Lazy
    def personId(self):
        return self.getPersonId()

    def getPersonId(self, userId=None):
        if userId is None:
            principal = getCurrentPrincipal()
        else:
            principal = getPrincipalForUserId(userId, context=self.context)
        if principal is not None:
            if IUnauthenticatedPrincipal.providedBy(principal):
                return None
            person = getPersonForUser(self.context, principal=principal)
            if person is None:
                return principal.id
            return util.getUidForObject(person)
        return None

