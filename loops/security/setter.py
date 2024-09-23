#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Base classes for security setters, i.e. adapters that provide standardized
methods for setting role permissions and other security-related stuff.
"""

from logging import getLogger
from zope.app.security.settings import Allow, Deny, Unset
from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, Interface
from zope.security.proxy import isinstance
from zope.securitypolicy.interfaces import \
                    IRolePermissionMap, IRolePermissionManager, \
                    IPrincipalRoleMap, IPrincipalRoleManager

from cybertools.meta.interfaces import IOptions
from cybertools.stateful.interfaces import IStateful
from loops.common import adapted, AdapterBase, baseObject
from loops.config.base import DummyOptions
from loops.interfaces import IConceptSchema, IBaseResourceSchema, ILoopsAdapter
from loops.organize.util import getPrincipalFolder, getGroupsFolder, getGroupId
from loops.security.common import overrides, setRolePermission, setPrincipalRole
from loops.security.common import allRolesExceptOwner, acquiringPredicateNames
from loops.security.common import getOption
from loops.security.interfaces import ISecuritySetter
from loops.versioning.interfaces import IVersionable

logger = getLogger('loops.security')


class BaseSecuritySetter(object):

    implements(ISecuritySetter)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    @Lazy
    def baseObject(self):
        return baseObject(self.context)

    @Lazy
    def adapted(self):
        return adapted(self.context)

    @Lazy
    def conceptManager(self):
        return self.baseObject.getLoopsRoot().getConceptManager()

    @Lazy
    def options(self):
        return IOptions(self.adapted)

    @Lazy
    def typeOptions(self):
        type = self.baseObject.getType()
        if type is None:
            return DummyOptions()
        return IOptions(adapted(type), DummyOptions())

    @Lazy
    def globalOptions(self):
        return IOptions(self.baseObject.getLoopsRoot())

    @Lazy
    def acquiringPredicates(self):
        return [self.conceptManager.get(n) for n in acquiringPredicateNames]

    def setDefaultRolePermissions(self):
        pass

    def setDefaultPrincipalRoles(self):
        pass

    def setDefaultSecurity(self):
        self.setDefaultRolePermissions()
        self.setDefaultPrincipalRoles()

    def setAcquiredSecurity(self, relation, revert=False, updated=None):
        pass

    def propagateSecurity(self, revert=False, updated=None):
        pass

    def acquireRolePermissions(self):
        pass

    def acquirePrincipalRoles(self):
        pass

    def copyPrincipalRoles(self, source, revert=False):
        pass


class LoopsObjectSecuritySetter(BaseSecuritySetter):

    parents = []

    @Lazy
    def rolePermissionManager(self):
        return IRolePermissionManager(self.baseObject)

    @Lazy
    def principalRoleManager(self):
        return IPrincipalRoleManager(self.baseObject)

    @Lazy
    def workspacePrincipals(self):
        gFolder = getGroupsFolder(self.baseObject, 'gloops_ws')
        if gFolder is None:
            return []
        return [getGroupId(g) for g in gFolder.values()]

    def setDefaultRolePermissions(self):
        rpm = self.rolePermissionManager
        for p, r, s in rpm.getRolesAndPermissions():
            setRolePermission(rpm, p, r, Unset)

    def setStateSecurity(self):
        statesDefs = (self.globalOptions('organize.stateful.concept', []) +
                      (self.typeOptions('organize.stateful') or []))
        for std in statesDefs:
            stf = component.getAdapter(self.baseObject, IStateful, name=std)
            stf.getStateObject().setSecurity(stf)

    def acquireRolePermissions(self):
        settings = {}
        #rpm = IRolePermissionMap(self.baseObject)
        #for p, r, s in rpm.getRolesAndPermissions():
        #    settings[(p, r)] = s
        for parent in self.parents:
            if parent == self.baseObject:
                continue
            if getOption(parent, 'security.no_propagate_rolepermissions', 
                         checkType=False):
                continue
            secProvider = parent
            wi = parent.workspaceInformation
            if wi:
                if wi.propagateRolePermissions == 'none':
                    continue
                if wi.propagateRolePermissions == 'workspace':
                    secProvider = wi
            rpm = IRolePermissionMap(secProvider)
            for p, r, s in rpm.getRolesAndPermissions():
                current = settings.get((p, r))
                if current is None or overrides(s, current):
                    if self.globalOptions('security.log_acquired_setting'):
                        logger.info('*** %s: %s, %s: current %s; new from %s: %s' %
                                (self.baseObject.__name__, p, r, current,
                                 parent.__name__, s))
                    settings[(p, r)] = s
        self.setDefaultRolePermissions()
        self.setRolePermissions(settings)
        self.setStateSecurity()

    def setRolePermissions(self, settings):
        for (p, r), s in settings.items():
            setRolePermission(self.rolePermissionManager, p, r, s)

    def acquirePrincipalRoles(self):
        #if baseObject(self.context).workspaceInformation:
        #    return      # do not remove/overwrite workspace settings
        settings = {}
        for parent in self.parents:
            if parent == self.baseObject:
                continue
            wi = parent.workspaceInformation
            if wi:
                if not wi.propagateParentSecurity:
                    continue
                prm = IPrincipalRoleMap(wi)
                for r, p, s in prm.getPrincipalsAndRoles():
                    current = settings.get((r, p))
                    if current is None or overrides(s, current):
                        settings[(r, p)] = s
            prm = IPrincipalRoleMap(parent)
            for r, p, s in prm.getPrincipalsAndRoles():
                current = settings.get((r, p))
                if current is None or overrides(s, current):
                    settings[(r, p)] = s
        self.setDefaultPrincipalRoles()
        for setter in self.versionSetters:
            setter.setPrincipalRoles(settings)

    @Lazy
    def versionSetters(self):
        return [self]

    def setDefaultPrincipalRoles(self):
        prm = self.principalRoleManager
        # TODO: set loops.Person roles for Person
        for r, p, s in prm.getPrincipalsAndRoles():
            if r in allRolesExceptOwner:
                setPrincipalRole(prm, r, p, Unset)

    def setPrincipalRoles(self, settings):
        prm = self.principalRoleManager
        for (r, p), s in settings.items():
            if r != 'loops.Owner':
                setPrincipalRole(prm, r, p, s)

    def copyPrincipalRoles(self, source, revert=False):
        prm = IPrincipalRoleMap(baseObject(source.context))
        for r, p, s in prm.getPrincipalsAndRoles():
            #if p in self.workspacePrincipals:
            if r != 'loops.Owner':
                if revert:
                    setPrincipalRole(self.principalRoleManager, r, p, Unset)
                else:
                    setPrincipalRole(self.principalRoleManager, r, p, s)


class ConceptSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IConceptSchema)

    @Lazy
    def noPropagateRolePermissions(self):
        return getOption(self.baseObject, 'security.no_propagate_rolepermissions', 
                         checkType=False)

    def setAcquiredSecurity(self, relation, revert=False, updated=None):
        if updated and relation.second in updated:
            return
        if relation.predicate not in self.acquiringPredicates:
            return
        setter = ISecuritySetter(adapted(relation.second))
        if not self.noPropagateRolePermissions:
            setter.setDefaultRolePermissions()
            setter.acquireRolePermissions()
        setter.acquirePrincipalRoles()
        #wi = baseObject(self.context).workspaceInformation
        #if wi and not wi.propagateParentSecurity:
        #     return
        #setter.copyPrincipalRoles(self, revert)
        #if wi: 
        #    setter.copyPrincipalRoles(ISecuritySetter(wi), revert)
        setter.propagateSecurity(revert, updated)

    def propagateSecurity(self, revert=False, updated=None):
        if self.globalOptions('noPropagateSecurity'):
            return
        if updated is None:
            updated = set()
        obj = self.baseObject
        updated.add(obj)
        for r in obj.getChildRelations(self.acquiringPredicates):
            self.setAcquiredSecurity(r, revert, updated)
        for r in obj.getResourceRelations(self.acquiringPredicates):
            self.setAcquiredSecurity(r, revert, updated)

    @Lazy
    def parents(self):
        return self.baseObject.getParents(self.acquiringPredicates)


class ResourceSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IBaseResourceSchema)

    @Lazy
    def parents(self):
        return self.baseObject.getConcepts(self.acquiringPredicates)

    def setStateSecurity(self):
        statesDefs = (self.globalOptions('organize.stateful.resource', []))
        for std in statesDefs:
            stf = component.getAdapter(self.baseObject, IStateful, name=std)
            stf.getStateObject().setSecurity(self.context)

    def setRolePermissions(self, settings):
        vSetters = [self]
        vr = IVersionable(baseObject(self.context))
        versions = list(vr.versions.values())
        if versions:
            vSetters = [ISecuritySetter(adapted(v)) for v in versions]
        for v in vSetters:
            for (p, r), s in settings.items():
                setRolePermission(v.rolePermissionManager, p, r, s)

    def copyPrincipalRoles(self, source, revert=False):
        vSetters = [self]
        vr = IVersionable(baseObject(self.context))
        versions = list(vr.versions.values())
        if versions:
            vSetters = [ISecuritySetter(adapted(v)) for v in versions]
        prm = IPrincipalRoleMap(baseObject(source.context))
        for r, p, s in prm.getPrincipalsAndRoles():
            #if p in self.workspacePrincipals:
            if r != 'loops.Owner' and p in self.workspacePrincipals:
                for v in vSetters:
                    if revert:
                        setPrincipalRole(v.principalRoleManager, r, p, Unset)
                    else:
                        setPrincipalRole(v.principalRoleManager, r, p, s)

    @Lazy
    def versionSetters(self):
        vr = IVersionable(baseObject(self.context))
        versions = list(vr.versions.values())
        if versions:
            return [ISecuritySetter(adapted(v)) for v in versions]
        return [self]
