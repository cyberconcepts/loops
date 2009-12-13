#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope.app.security.settings import Allow, Deny, Unset
from zope.app.securitypolicy.interfaces import \
                    IRolePermissionMap, IRolePermissionManager, \
                    IPrincipalRoleMap, IPrincipalRoleManager
from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, Interface
from zope.security.proxy import isinstance

from loops.common import adapted, AdapterBase, baseObject
from loops.organize.util import getPrincipalFolder, getGroupsFolder, getGroupId
from loops.security.common import overrides, setRolePermission, setPrincipalRole
from loops.interfaces import IConceptSchema, IBaseResourceSchema, ILoopsAdapter
from loops.security.interfaces import ISecuritySetter


class BaseSecuritySetter(object):

    implements(ISecuritySetter)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    @Lazy
    def baseObject(self):
        return baseObject(self.context)

    @Lazy
    def conceptManager(self):
        return self.baseObject.getLoopsRoot().getConceptManager()

    @Lazy
    def acquiringPredicates(self):
        names = ('hasType', 'standard',)
        return [self.conceptManager.get(n) for n in names]

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

    def acquireRolePermissions(self):
        settings = {}
        for p in self.parents:
            if p == self.baseObject:
                continue
            secProvider = p
            wi = p.workspaceInformation
            if wi:
                if wi.propagateRolePermissions == 'none':
                    continue
                if wi.propagateRolePermissions == 'workspace':
                    secProvider = wi
            rpm = IRolePermissionMap(secProvider)
            for p, r, s in rpm.getRolesAndPermissions():
                current = settings.get((p, r))
                if current is None or overrides(s, current):
                    settings[(p, r)] = s
        self.setDefaultRolePermissions()
        for (p, r), s in settings.items():
            setRolePermission(self.rolePermissionManager, p, r, s)

    def copyPrincipalRoles(self, source, revert=False):
        prm = IPrincipalRoleMap(baseObject(source.context))
        for r, p, s in prm.getPrincipalsAndRoles():
            if p in self.workspacePrincipals:
                if revert:
                    setPrincipalRole(self.principalRoleManager, r, p, Unset)
                else:
                    setPrincipalRole(self.principalRoleManager, r, p, s)


class ConceptSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IConceptSchema)

    def setAcquiredSecurity(self, relation, revert=False, updated=None):
        if updated and relation.second in updated:
            return
        if relation.predicate not in self.acquiringPredicates:
            return
        setter = ISecuritySetter(adapted(relation.second))
        setter.setDefaultRolePermissions()
        setter.acquireRolePermissions()
        setter.copyPrincipalRoles(self, revert)
        setter.propagateSecurity(revert, updated)

    def propagateSecurity(self, revert=False, updated=None):
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

