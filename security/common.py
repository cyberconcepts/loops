#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
Common functions and other stuff for working with permissions and roles.
"""

from persistent import Persistent
from zope import component
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.security.settings import Allow, Deny, Unset
from zope.app.securitypolicy.interfaces import IPrincipalRoleManager
from zope.app.securitypolicy.interfaces import IRolePermissionManager
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.lifecycleevent import IObjectCreatedEvent, IObjectModifiedEvent
from zope.security import canAccess, canWrite
from zope.security import checkPermission as baseCheckPermission
from zope.security.management import getInteraction
from zope.traversing.api import getName
from zope.traversing.interfaces import IPhysicallyLocatable

from cybertools.meta.interfaces import IOptions
from loops.common import adapted
from loops.interfaces import ILoopsObject, IConcept
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.security.interfaces import ISecuritySetter, IWorkspaceInformation


allRolesExceptOwner = (
        #'zope.SiteManager' - no, not this one...
        'zope.Anonymous', 'zope.Member', 'zope.ContentManager', 'loops.Staff',
        'loops.xmlrpc.ConceptManager', # relevant for local security?
        #'loops.SiteManager',
        'loops.Person', 'loops.Member', 'loops.Master')
allRolesExceptOwnerAndMaster = tuple(allRolesExceptOwner[:-1])
minorPrivilegedRoles = ('zope.Anonymous', 'zope.Member',)
localRoles = ('zope.Anonymous', 'zope.Member', 'zope.ContentManager',
        'loops.SiteManager', 'loops.Staff', 'loops.Member', 'loops.Master',
        'loops.Owner', 'loops.Person')

localPermissions = ('zope.ManageContent', 'zope.View', 'loops.ManageWorkspaces',
        'loops.ViewRestricted', 'loops.EditRestricted', 'loops.AssignAsParent',)

acquiringPredicateNames = ('hasType', 'standard', 'ownedby', 'ispartof')

allocationPredicateNames = ('isowner', 'ismaster', 'ismember',)

workspaceGroupsFolderName = 'gloops_ws'


# checking and querying functions

def getOption(obj, option, checkType=True):
    opts = component.queryAdapter(adapted(obj), IOptions)
    if opts is not None:
        opt = opts(option, None)
        if opt:
            return opt[0]
    if not checkType:
        return None
    typeMethod = getattr(obj, 'getType', None)
    if typeMethod is not None:
        opts = component.queryAdapter(adapted(typeMethod()), IOptions)
        if opts is not None:
            opt = opts(option, [None])
            if opt:
                return opt[0]
    return None

def canAccessObject(obj):
    if not canAccess(obj, 'title'):
        return False
    perm = getOption(obj, 'access_permission')
    if not perm:
        return True
    return checkPermission(perm, obj)

def canListObject(obj, noCheck=False):
    if noCheck:
        return True
    return canAccessObject(obj)

def canAccessRestricted(obj):
    return checkPermission('loops.ViewRestricted', obj)

def canWriteObject(obj):
    return canWrite(obj, 'title') or canAssignAsParent(obj) 

def canEditRestricted(obj):
    return checkPermission('loops.EditRestricted', obj)

def canAssignAsParent(obj):
    return checkPermission('loops.AssignAsParent', obj)

def checkPermission(permission, obj):
    return baseCheckPermission(permission, obj)


def getCurrentPrincipal():
    interaction = getInteraction()
    if interaction is not None:
        parts = interaction.participations
        if parts:
            return parts[0].principal
    return None


# functions for checking and setting security properties

def overrides(s1, s2):
    settings = [Allow, Deny, Unset]
    return settings.index(s1) < settings.index(s2)

def setRolePermission(rpm, p, r, setting):
    if setting == Allow:
        rpm.grantPermissionToRole(p, r)
    elif setting == Deny:
        rpm.denyPermissionToRole(p, r)
    else:
        rpm.unsetPermissionFromRole(p, r)

def setPrincipalRole(prm, r, p, setting):
    if setting == Allow:
        prm.assignRoleToPrincipal(r, p)
    elif setting == Deny:
        prm.removeRoleFromPrincipal(r, p)
    else:
        prm.unsetRoleForPrincipal(r, p)


def assignOwner(obj, principalId):
    prm = IPrincipalRoleManager(obj, None)
    if prm is not None:
        prm.assignRoleToPrincipal('loops.Owner', principalId)

def removeOwner(obj, principalId):
    prm = IPrincipalRoleManager(obj, None)
    if prm is not None:
        prm.unsetRoleForPrincipal('loops.Owner', principalId)

def assignPersonRole(obj, principalId):
    prm = IPrincipalRoleManager(obj)
    prm.assignRoleToPrincipal('loops.Person', principalId)

def removePersonRole(obj, principalId):
    prm = IPrincipalRoleManager(obj)
    prm.unsetRoleForPrincipal('loops.Person', principalId)


def allowEditingForOwner(obj, deny=allRolesExceptOwner, revert=False):
    rpm = IRolePermissionManager(obj)
    if revert:
        for role in deny:
            rpm.unsetPermissionFromRole('zope.ManageContent', role)
        rpm.unsetPermissionFromRole('zope.ManageContent', 'loops.Owner')
    else:
        for role in deny:
            rpm.denyPermissionToRole('zope.ManageContent', role)
        rpm.grantPermissionToRole('zope.ManageContent', 'loops.Owner')


def restrictView(obj, roles=allRolesExceptOwnerAndMaster, revert=False):
    rpm = IRolePermissionManager(obj)
    if revert:
        for role in roles:
            rpm.unsetPermissionFromRole('zope.View', role)
    else:
        for role in roles:
            rpm.denyPermissionToRole('zope.View', role)


# event handlers

#@component.adapter(ILoopsObject, IObjectAddedEvent)
#@component.adapter(ILoopsObject, IObjectModifiedEvent)
@component.adapter(ILoopsObject, IObjectCreatedEvent)
def setDefaultSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setDefaultSecurity()
    principal = getCurrentPrincipal()
    if principal is not None:
        assignOwner(obj, principal.id)


@component.adapter(IConcept, IAssignmentEvent)
def grantAcquiredSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setAcquiredSecurity(event.relation)


@component.adapter(IConcept, IDeassignmentEvent)
def revokeAcquiredSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setAcquiredSecurity(event.relation, revert=True)


# workspace handling

class WorkspaceInformation(Persistent):
    """ For storing security-related stuff pertaining to
        children and resources of the context (=parent) object.
    """

    implements(IPhysicallyLocatable, IWorkspaceInformation)

    __name__ = u'workspace_information'

    #propagateRolePermissions = 'object'   # or 'none'
    propagateRolePermissions = 'workspace'
    propagateParentSecurity = True  # False
    #propagateParentSecurity = False
    allocationPredicateNames = allocationPredicateNames
    workspaceGroupsFolderName = workspaceGroupsFolderName

    def __init__(self, parent):
        self.__parent__ = parent
        self.workspaceGroupNames = {}

    def getName(self):
        return self.__name__

    def getParent(self):
        return self.__parent__


def getWorkspaceGroup(obj, predicate):
    wsi = obj.workspaceInformation
    if wsi is None:
        return None
    pn = getName(predicate)
    if pn in wsi.allocationPredicateNames:
        gn = wsi.workspaceGroupNames
        if not isinstance(gn, dict):    # backwards compatibility
            return None
        groupName = gn.get(pn)
        if groupName:
            gfName = wsi.workspaceGroupsFolderName
            if gfName:
                from loops.organize.util import getGroupsFolder
                gf = getGroupsFolder(wsi, gfName)
                if gf is not None:
                    return gf.get(groupName)
    return None


@component.adapter(ILoopsObject, IAssignmentEvent)
def addGroupMembershipOnAssignment(obj, event):
    group = getWorkspaceGroup(obj, event.relation.predicate)
    if group is not None:
        person = adapted(event.relation.second)
        from loops.organize.interfaces import IPerson
        if IPerson.providedBy(person):
            userId = person.getUserId()
            if userId:
                members = list(group.principals)
                if userId not in members:
                    members.append(userId)
                    group.principals = tuple(members)
                #print '*** assign', group.__name__, userId, group.principals

@component.adapter(ILoopsObject, IDeassignmentEvent)
def removeGroupMembershipOnDeassignment(obj, event):
    group = getWorkspaceGroup(obj, event.relation.predicate)
    if group is not None:
        person = adapted(event.relation.second)
        from loops.organize.interfaces import IPerson
        if IPerson.providedBy(person):
            userId = person.getUserId()
            if userId:
                members = list(group.principals)
                if userId in members:
                    members.remove(userId)
                    group.principals = tuple(members)
                #print '*** remove', group.__name__, userId, group.principals
