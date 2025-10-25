# loops.server.auth

# provide (register) authentication utility
# and other authentication and authorization stuff.

from scopes.web.auth import oidc
from zope.authentication.interfaces import IAuthentication
from zope.browserpage import ViewPageTemplateFile
from zope.component import provideAdapter, getUtility, provideUtility
from zope.interface import implementer, Interface
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserPage
from zope.publisher.browser import BrowserPage
from zope.security.proxy import removeSecurityProxy

import config

def registerAuthUtility(config):
    baseAuth = getUtility(IAuthentication)
    print('*** registerAuthUtility, baseAuth:', baseAuth)
    provideUtility(oidc.OidcAuthentication(baseAuth))


class LoginPage:

    index = ViewPageTemplateFile('loginform.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.authMethod = getattr(config, 'authentication_method', 'legacy')
        if self.authMethod == 'cookie':
            self.authMethod = getAuthMethodCookieValue(request)
        self.oidc_allowed = self.authMethod in ('oidc', 'select')

    def __call__(self):
        print('***', self.request.principal.id)
        print('***', self.authMethod)
        if self.authMethod == 'oidc':
            return self.authOidc()
        return self.index()

    def authOidc(self):
        oidc.Authenticator(self.request).login()
        return ''

def getAuthMethodCookieValue(request):
    print('***', dict(request.cookies))
    return request.cookies.get('loops_auth_method') or 'legacy'


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
