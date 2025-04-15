# loops.server.auth

# provide (register) authentication utility
# and other authentication and authorization stuff.

from scopes.server import auth
from zope.authentication.interfaces import IAuthentication
from zope.component import provideAdapter, getUtility, provideUtility
from zope.interface import implementer, Interface
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserPage
from zope.publisher.browser import BrowserPage
from zope.security.proxy import removeSecurityProxy

def registerAuthUtility(config):
    baseAuth = getUtility(IAuthentication)
    print('*** registerAuthUtility, baseAuth:', baseAuth)
    provideUtility(auth.OidcAuthentication(baseAuth))


class LoginView:

    def __call__(self):
        auth.Authenticator(self.request).login()
        return ''


class CallbackView:

    def __call__(self):
        auth.Authenticator(self.request).callback()
        return ''
