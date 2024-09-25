# loops.browser.auth

""" Login, logout, unauthorized stuff.
"""

from zope.app.exception.browser.unauthorized import Unauthorized as DefaultUnauth
from zope.authentication.interfaces import IAuthentication
from zope.authentication.interfaces import ILogout, IUnauthenticatedPrincipal
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.interface import implementer

from loops.browser.concept import ConceptView
from loops.browser.node import NodeView


template = ViewPageTemplateFile('auth.pt')


class LoginConcept(ConceptView):

    template = template

    @Lazy
    def macro(self):
        return self.template.macros['login_form']


class LoginForm(NodeView):

    template = template

    @Lazy
    def macro(self):
        return self.template.macros['login_form']

    @Lazy
    def item(self):
        return self


@implementer(ILogout)
class Logout(object):


    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        nextUrl = self.request.get('nextURL') or self.request.URL[-1]
        if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
            auth = component.getUtility(IAuthentication)
            ILogout(auth).logout(self.request)
        return self.request.response.redirect(nextUrl)


class Unauthorized(ConceptView):

    isTopLevel = True

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        response = self.request.response
        response.setStatus(403)
        # make sure that squid does not keep the response in the cache
        response.setHeader('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT')
        response.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
        response.setHeader('Pragma', 'no-cache')
        if self.nodeView is None:
            v = DefaultUnauth(self.context, self.request)
            return v()
        url = self.nodeView.topMenu.url
        response.redirect(url + '/unauthorized')
