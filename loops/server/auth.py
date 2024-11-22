# loops.server.auth

# provide (register) authentication utility
# and other authentication and authorization stuff.

from scopes.server import auth
from zope.authentication.interfaces import IAuthentication
from zope.component import getUtility, provideUtility

def registerAuthUtility(config):
    baseAuth = getUtility(IAuthentication)
    print('*** registerAuthUtility, baseAuth:', baseAuth)
    provideUtility(auth.JwtAuthentication(baseAuth))
    
