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
Base class(es) for track/record managers.

$Id$
"""

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
            person = getPersonForUser(self.context, principal=principal)
            if person is None:
                return principal.id
            return util.getUidForObject(person)
        return None

