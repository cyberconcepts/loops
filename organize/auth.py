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
Specialized authentication components.

$Id$
"""

from persistent import Persistent
from zope.app.container.contained import Contained
from zope import component
from zope.interface import implements
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import PrincipalInfo
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.security.interfaces import IAuthentication
from zope.cachedescriptors.property import Lazy


class PersonBasedAuthenticator(Persistent, Contained):

    implements(IAuthenticatorPlugin)

    def __init__(self, prefix=''):
        self.prefix = unicode(prefix)

    def authenticateCredentials(self, credentials):
        if not isinstance(credentials, dict):
            return None
        login = credentials.get('login')
        password = credentials.get('password')
        if not login or not password :
            return None
        id = self.prefix + login
        if self._checkPassword(id, password):
            return PrincipalInfo(id, login, login, u'')
        return None

    def principalInfo(self, id):
        if id.startswith(self.prefix):
            login = id[len(self.prefix):]
            if login:
                return PrincipalInfo(id, login, login, u'')

    def setPassword(self, login, password):
        id = self.prefix + login
        pa = self.getPrincipalAnnotations(id)
        pa['loops.organize.password'] = password

    @Lazy
    def principalAnnotations(self):
        return component.getUtility(IPrincipalAnnotationUtility)

    def getPrincipalAnnotations(id):
        return self.principalAnnotations.getAnnotationsById(id)

    def _checkPassword(self, id, password):
        pa = self.getPrincipalAnnotations(id)
        return pa.get('loops.organize.password') == password

