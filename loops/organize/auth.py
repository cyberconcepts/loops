# loops.organize.auth

""" Specialized authentication components.
"""

from persistent import Persistent
from zope.authentication.interfaces import IAuthentication
from zope.container.contained import Contained
from zope import component
from zope.interface import Interface, implementer
from zope.pluggableauth.factories import PrincipalInfo
from zope.pluggableauth.interfaces import IAuthenticatorPlugin
from zope.pluggableauth.plugins.principalfolder import IInternalPrincipal
from zope.principalannotation.interfaces import IPrincipalAnnotationUtility
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


@implementer(IAuthenticatorPlugin, IPersonBasedAuthenticator)
class PersonBasedAuthenticator(Persistent, Contained):

    passwordKey = 'loops.organize.password'
    ignoreCase = True

    def __init__(self, prefix=''):
        self.prefix = prefix

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

    def getPassword(self, login):
        pa = self.getPrincipalAnnotations(
                        getParent(self).prefix + self.prefix + login)
        return pa.get(self.passwordKey)

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

