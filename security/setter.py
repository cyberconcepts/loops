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
from zope.app.securitypolicy.interfaces import IRolePermissionMap
from zope.app.securitypolicy.interfaces import IRolePermissionManager
from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, Interface
from zope.security.proxy import isinstance

from loops.common import adapted, AdapterBase
from loops.security.common import overrides, setRolePermission
from loops.interfaces import IConceptSchema, IBaseResourceSchema, ILoopsAdapter
from loops.security.interfaces import ISecuritySetter


class BaseSecuritySetter(object):

    implements(ISecuritySetter)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    def setDefaultRolePermissions(self):
        pass

    def setDefaultPrincipalRoles(self):
        pass

    def acquireRolePermissions(self):
        pass

    def setAcquiredRolePermissions(self, relation, revert=False, updated=None):
        pass

    def setAcquiredPrincipalRoles(self, relation, revert=False, updated=None):
        pass

    def propagateRolePermissions(self, updated=None):
        pass

    def propagatePrincipalRoles(self, updated=None):
        pass


class LoopsObjectSecuritySetter(BaseSecuritySetter):

    parents = []

    @Lazy
    def baseObject(self):
        obj = self.context
        if isinstance(obj, AdapterBase):
            obj = obj.context
        return obj

    @Lazy
    def rolePermissionManager(self):
        return IRolePermissionManager(self.baseObject)

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


class ConceptSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IConceptSchema)

    def setAcquiredRolePermissions(self, relation, revert=False, updated=None):
        if updated and relation.second in updated:
            return
        setter = ISecuritySetter(adapted(relation.second), None)
        if setter is not None:
            setter.acquireRolePermissions()
            setter.propagateRolePermissions(updated)

    def setAcquiredPrincipalRoles(self, relation, revert=False, updated=None):
        pass

    def propagateRolePermissions(self, updated=None):
        if updated is None:
            updated = set()
        obj = self.baseObject
        updated.add(obj)
        for r in obj.getChildRelations():
            self.setAcquiredRolePermissions(r, updated=updated)
        for r in obj.getResourceRelations():
            self.setAcquiredRolePermissions(r, updated=updated)

    def propagatePrincipalRoles(self, updated=None):
        pass

    @Lazy
    def parents(self):
        return self.baseObject.getParents()


class ResourceSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IBaseResourceSchema)

    @Lazy
    def parents(self):
        return self.baseObject.getConcepts()

