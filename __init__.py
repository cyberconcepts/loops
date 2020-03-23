# package loops

# intid monkey patch for avoiding ForbiddenAttribute error

from zope import component
from zope.intid.interfaces import IIntIds
from zope import intid
from zope.security.proxy import removeSecurityProxy

def queryId(self, ob, default=None):
    try:
        return self.getId(removeSecurityProxy(ob))
    except KeyError:
        return default

intid.IntIds.queryId = queryId

