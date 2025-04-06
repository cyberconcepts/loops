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

def registerAuthentication(config):
    registerAuthUtility(config)
    #registerAuthViews(config)

def registerAuthUtility(config):
    baseAuth = getUtility(IAuthentication)
    print('*** registerAuthUtility, baseAuth:', baseAuth)
    provideUtility(auth.OidcAuthentication(baseAuth))

def registerAuthViews(config):
    provideAdapter(LoginView, (Interface, IBrowserRequest), IBrowserPage,
                   name='auth_login')
    provideAdapter(callback, (Interface, IBrowserRequest), IBrowserPage,
                   name='auth_callback')

@implementer(IBrowserPage)
def login(context, request):
    removeSecurityProxy(context)
    auth.Authenticator(request).login()
    return context

@implementer(IBrowserPage)
def callback(context, request):
    removeSecurityProxy(context)
    auth.Authenticator(request).callback()
    return DummyView(context, request)


class LoginView:

    def __call__(self):
        auth.Authenticator(self.request).login()
        return ''


class CallbackView:

    def __call__(self):
        auth.Authenticator(self.request).callback()
        return ''
