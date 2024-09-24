# loops.security.policy

""" A loops-specific security policy. Intended mainly to deal with checking
concept map parents in addition to containers for collecting principal roles.
"""

from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import classImplements
from zope.security.interfaces import ISecurityPolicy
from zope.security.proxy import removeSecurityProxy
from zope.securitypolicy.interfaces import IPrincipalRoleMap, IRolePermissionMap
from zope.securitypolicy.settings import Allow, Deny, Unset
from zope.securitypolicy.zopepolicy import ZopeSecurityPolicy
from zope.securitypolicy.zopepolicy import SettingAsBoolean, \
                        globalRolesForPrincipal, globalRolesForPermission

from loops.interfaces import IConcept, IResource


class LoopsSecurityPolicy(ZopeSecurityPolicy):

    classImplements(ISecurityPolicy)

    def cached_principal_roles(self, obj, principal, checked=None):
        if checked is None:
            checked = []
        obj = removeSecurityProxy(obj)
        cache = self.cache(obj)
        try:
            cache_principal_roles = cache.principal_roles
        except AttributeError:
            cache_principal_roles = cache.principal_roles = {}
        try:
            return cache_principal_roles[principal]
        except KeyError:
            pass
        if obj is None:
            roles = dict([(role, SettingAsBoolean[setting])
                            for (role, setting)
                                    in globalRolesForPrincipal(principal)])
            roles['zope.Anonymous'] = True # Everybody has Anonymous
            cache_principal_roles[principal] = roles
            return roles
        roles = {}
        for p in self.getParents(obj, checked):
            # TODO: care for correct combination if there is more than
            # one parent
            if p is not None:
                roles.update(self.cached_principal_roles(p, principal, checked))
        if not roles:
            roles = self.cached_principal_roles(None, principal, checked)
        prinrole = IPrincipalRoleMap(obj, None)
        if prinrole:
            roles = roles.copy()
            for role, setting in prinrole.getRolesForPrincipal(principal):
                roles[role] = SettingAsBoolean[setting]
        cache_principal_roles[principal] = roles
        return roles

    def cached_roles(self, obj, permission, checked=None):
        if checked is None:
            checked = []
        obj = removeSecurityProxy(obj)
        cache = self.cache(obj)
        try:
            cache_roles = cache.roles
        except AttributeError:
            cache_roles = cache.roles = {}
        try:
            return cache_roles[permission]
        except KeyError:
            pass
        if obj is None:
            roles = dict([(role, 1)
                            for (role, setting)
                                    in globalRolesForPermission(permission)
                            if setting is Allow])
            cache_roles[permission] = roles
            return roles
        roles = {}
        for p in self.getParents(obj, checked):
            # TODO: care for correct combination if there is more than
            # one parent
            if p is not None:
                roles.update(self.cached_roles(p, permission, checked))
        if not roles:
            roles = self.cached_roles(None, permission, checked)
        roleper = IRolePermissionMap(obj, None)
        if roleper:
            roles = roles.copy()
            for role, setting in roleper.getRolesForPermission(permission):
                if setting is Allow:
                    roles[role] = 1
                elif role in roles:
                    del roles[role]

        cache_roles[permission] = roles
        return roles

    def getParents(self, obj, checked):
        if obj in checked:      # cycle - leave the concept map
            parent = getattr(obj, '__parent__', None)
            return [parent]
        # keep concept parents in cache
        cache = self.cache(obj)
        try:
            parents = cache.parents
        except AttributeError:
            parents = []
            if IConcept.providedBy(obj) or IResource.providedBy(obj):
                try:
                    parents.append(obj.getType())
                except AttributeError:
                    pass
                except TypeError:
                    from logging import getLogger
                    getLogger('loops.security.policy').warn(
                                    'TypeError: %s.getType: %r' % (obj, obj.getType))
            #if IConcept.providedBy(obj):
            #    parents = [p for p in obj.getParents(noSecurityCheck=True)
            #                 if p != obj]
            #elif IResource.providedBy(obj):
            #    parents = [p for p in obj.getConcepts(noSecurityCheck=True)
            #                 if p != obj]
            cache.parents = parents
        if not parents:
            parents = [getattr(obj, '__parent__', None)]
        checked.append(obj)
        return parents
