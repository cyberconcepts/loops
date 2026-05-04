# loops.server.auth

# provide (register) authentication utility
# and other authentication and authorization stuff.

from scopes.web.auth import oidc
from zope.authentication.interfaces import IAuthentication, IUnauthenticatedPrincipal
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import provideAdapter, getUtility, provideUtility
from zope.interface import implementer, Interface
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserPage
from zope.publisher.browser import BrowserPage
from zope.security.proxy import removeSecurityProxy

import config

from logging import getLogger
logger = getLogger("loops.server.auth")

def registerAuthUtility(config):
    baseAuth = getUtility(IAuthentication)
    print('*** registerAuthUtility, baseAuth:', baseAuth)
    provideUtility(oidc.OidcAuthentication(baseAuth))


class LoginPage:

    index = ViewPageTemplateFile('loginform.pt')
    showSelection = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.authMethod = getConfigAuthMethod()
        if self.authMethod == 'cookie':
            self.authMethod = getAuthMethodCookieValue(request)
        self.oidc_allowed = self.showSelection or self.authMethod in ('oidc', 'select')

    def __call__(self):
        if self.authMethod == 'oidc' and not self.showSelection:
            return self.authOidc()
        return self.index()

    @Lazy
    def isAnonymous(self):
        return IUnauthenticatedPrincipal.providedBy(self.request.principal)

    def authOidc(self):
        oidc.Authenticator(self.request).login()
        return ''


class LoginPageSelect(LoginPage):

    @property
    def showSelection(self):
        return getConfigAuthMethod() == 'cookie'

    def authMethodCookieString(self):
        domain = getattr(config, 'authentication_method_cookie_domain', None)
        return 'document.cookie=`loops_auth_method=${this.value}; path=/; expires=Sun, 31 Jan 2027 12:00:00 UTC%s`' % (domain and f'; domain={domain}' or '')


class Unauthorized(LoginPage):

    def __call__(self):
        response = self.request.response
        # make sure that squid does not keep the response in the cache
        response.setHeader('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT')
        response.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
        response.setHeader('Pragma', 'no-cache')
        logger.warn(f'unauthorized: user={self.request.principal.id}, authMethod={self.authMethod}')
        if self.isAnonymous:
            return super(Unauthorized, self).__call__()  # open or redirect to login page
        else:
            response.setStatus(403)
            return 'Unauthorized: You are not allowed to access this ressource.'


def getConfigAuthMethod():
    return getattr(config, 'authentication_method', 'legacy')

def getAuthMethodCookieValue(request):
    default = getattr(config, 'authentication_method_cookie_default', 'legacy')
    return request.cookies.get('loops_auth_method') or default


# OIDC authentication

class LoginView(LoginPage):

    def __call__(self):
        return self.authOidc()


class CallbackView:

    def __call__(self):
        oidc.Authenticator(
                self.request).callback(groupsProvider=self.getGroupsForPrincipal)
        return ''

    def getGroupsForPrincipal(self, prcId):
        pau = getUtility(IAuthentication, context=self.context)
        groups = pau['gloops'].getGroupsForPrincipal(prcId)
        gf_ws = pau.get('gloops_ws')
        if gf_ws:
            groups += gf_ws.getGroupsForPrincipal(prcId)
        return groups


class LogoutView:

    def __call__(self):
        oidc.Authenticator(self.request).logout()
        return ''
