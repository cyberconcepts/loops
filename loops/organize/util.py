# loops.organize.util

""" Utilities for the loops.organize package.
"""

from zope import interface, component, schema
from zope.authentication.interfaces import IAuthentication, PrincipalLookupError
from zope.component import queryNextUtility
from zope.pluggableauth.interfaces import IPluggableAuthentication
from zope.pluggableauth.interfaces import IAuthenticatorPlugin
from zope.pluggableauth.plugins.groupfolder import GroupFolder
from zope.securitypolicy.interfaces import IPrincipalRoleManager
from zope.securitypolicy.settings import Allow, Deny, Unset
from zope.traversing.api import getParents
from loops.common import adapted
from loops.security.common import getCurrentPrincipal
from loops.type import getOptionsDict

defaultAuthPluginId = 'loops'


def getPrincipalFolder(context=None, authPluginId=None, ignoreErrors=False):
    pau = component.getUtility(IAuthentication, context=context)
    if not IPluggableAuthentication.providedBy(pau):
        if ignoreErrors:
            return None
        raise ValueError(u'There is no pluggable authentication '
                          'utility available.')
    if authPluginId is None and context is not None:
        person = context.getLoopsRoot().getConceptManager()['person']
        od = getOptionsDict(adapted(person).options)
        authPluginId = od.get('principalfolder', defaultAuthPluginId)
    if authPluginId is None:
        authPluginId = defaultAuthPluginId
    if authPluginId not in pau.authenticatorPlugins:
        if ignoreErrors:
            return None
        raise ValueError(u"There is no loops authenticator "
                          "plugin '%s' available." % authPluginId)
    for name, plugin in pau.getAuthenticatorPlugins():
        if name == authPluginId:
            return plugin


def getGroupsFolder(context=None, name='gloops', create=False):
    gf = getPrincipalFolder(authPluginId=name, ignoreErrors=True)
    if gf is None and create:
        pau = component.getUtility(IAuthentication, context=context)
        gf = pau[name] = GroupFolder(name + '.')
        pau.authenticatorPlugins = tuple(
                        list(pau.authenticatorPlugins) + [name])
    return gf


def getGroupId(group):
    gf = group.__parent__
    return ''.join((gf.__parent__.prefix, gf._groupid(group)))


def getInternalPrincipal(id, context=None, pau=None):
    if pau is None:
        pau = component.getUtility(IAuthentication, context=context)
    if not IPluggableAuthentication.providedBy(pau):
        raise ValueError(u'There is no pluggable authentication '
                         u'utility available.')
    if not id.startswith(pau.prefix):
        next = queryNextUtility(pau, IAuthentication)
        if next is None:
            raise PrincipalLookupError(id)
        #return next.getPrincipal(id)
        return getInternalPrincipal(id, context, pau=next)
    id = id[len(pau.prefix):]
    for name, authplugin in pau.getAuthenticatorPlugins():
        if not id.startswith(authplugin.prefix):
            continue
        principal = authplugin.get(id[len(authplugin.prefix):])
        if principal is None:
            continue
        return principal
    next = queryNextUtility(pau, IAuthentication)
    if next is not None:
        #return next.getPrincipal(pau.prefix + id)
        return getInternalPrincipal(id, context, pau=next)
    raise PrincipalLookupError(id)


def getPrincipalForUserId(id, context=None):
    auth = component.getUtility(IAuthentication, context=context)
    try:
        return auth.getPrincipal(id)
    except PrincipalLookupError:
        return None


def getRolesForPrincipal(id, context):
    prinrole = IPrincipalRoleManager(context, None)
    if prinrole is None:
        return []
    result = []
    denied = []
    for role, setting in prinrole.getRolesForPrincipal(id):
        if setting == Allow:
            result.append(role)
        elif setting == Deny:
            denied.append(role)
    for obj in getParents(context):
        prinrole = IPrincipalRoleManager(obj, None)
        if prinrole is not None:
            for role, setting in prinrole.getRolesForPrincipal(id):
                if setting == Allow and role not in denied and role not in result:
                    result.append(role)
                elif setting == Deny and role not in denied:
                    denied.append(role)
    return result


def getGroupsForPrincipal(principal=None):
    if principal is None:
        principal = getCurrentPrincipal()
    gf = getGroupsFolder()
    if gf is None:
        return []
    prefix = 'gloops.'
    return [(g.startswith(prefix) and g[len(prefix):] or g)
            for g in gf.getGroupsForPrincipal(principal.id)]


def getTrackingStorage(obj, name):
    records = obj.getLoopsRoot().getRecordManager()
    if records is not None:
        return records.get(name)
    return None

