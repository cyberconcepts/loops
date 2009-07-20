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
from zope.interface import Interface, implements
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import IInternalPrincipal
from zope.app.authentication.principalfolder import PrincipalInfo
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.security.interfaces import IAuthentication
from zope import schema
from zope.traversing.api import getParent

from cybertools.browser.loops.auth import LoopsSessionCredentialsPlugin \
                            as BaseSessionCredentialsPlugin
from loops.organize.interfaces import IPresence
from loops.util import _


class IPersonBasedAuthenticator(Interface):

    prefix = schema.TextLine(
        title=_("Prefix"),
        description=_(
        "Prefix to be added to all principal ids to assure "
        "that all ids are unique within the authentication service"),
        missing_value=u"",
        default=u'',
        readonly=True)


class PersonBasedAuthenticator(Persistent, Contained):

    implements(IAuthenticatorPlugin, IPersonBasedAuthenticator)

    passwordKey = 'loops.organize.password'
    ignoreCase = True

    def __init__(self, prefix=''):
        self.prefix = unicode(prefix)

    def authenticateCredentials(self, credentials):
        if not isinstance(credentials, dict):
            return None
        login = credentials.get('login')
        password = credentials.get('password')
        if self.checkPassword(login, password):
            return PrincipalInfo(self.prefix + login, login, login, u'')
        return None

    def principalInfo(self, id):
        if id.startswith(self.prefix):
            login = id[len(self.prefix):]
            if login:
                return PrincipalInfo(id, login, login, u'')

    def checkPassword(self, login, password):
        if login and password:
            pa = self.getPrincipalAnnotations(
                        getParent(self).prefix + self.prefix + login)
            if self.ignoreCase:
                password = password.lower()
            return pa.get(self.passwordKey) == password
        return None

    def setPassword(self, login, password):
        if self.ignoreCase:
            password = password.lower()
        pa = self.getPrincipalAnnotations(
                        getParent(self).prefix + self.prefix + login)
        pa[self.passwordKey] = password

    def getPrincipalAnnotations(self, id):
        utility = component.getUtility(IPrincipalAnnotationUtility)
        return utility.getAnnotationsById(id)

    def get(self, login):
        return InternalPrincipal(self, login)


class LoopsSessionCredentialsPlugin(BaseSessionCredentialsPlugin):

    def logout(self, request):
        presence = component.getUtility(IPresence)
        presence.removePresentUser(request.principal.id)
        super(LoopsSessionCredentialsPlugin, self).logout(request)


class InternalPrincipal(object):

    def __init__(self, auth, login):
        self.auth = auth
        self.login = login

    def checkPassword(self, password):
        return self.auth.checkPassword(self.login, password)

    def setPassword(self, passowrd):
        self.auth.setPassword(self.login, password)

