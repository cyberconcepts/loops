#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope import component
from zope.app.securitypolicy.interfaces import IPrincipalRoleManager
from zope.app.securitypolicy.interfaces import IRolePermissionManager
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.lifecycleevent import IObjectCreatedEvent
from zope.security import canAccess, canWrite
from zope.security import checkPermission as baseCheckPermission
from zope.security.management import getInteraction

from loops.common import adapted
from loops.interfaces import ILoopsObject, IConcept
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.security.interfaces import ISecuritySetter


allRolesExceptOwner = (
        #'zope.SiteManager' - no, not this one...
        'zope.Anonymous', 'zope.Member', 'zope.ContentManager', 'loops.Staff',
        'loops.xmlrpc.ConceptManager', # relevant for local security?
        #'loops.SiteManager',
        'loops.Master',)
allRolesExceptOwnerAndMaster = tuple(allRolesExceptOwner[:-1])
minorPrivilegedRoles = ('zope.Anonymous', 'zope.Member',)


# checking and querying functions

def canAccessObject(obj):
    return canAccess(obj, 'title')

def canListObject(obj, noCheck=False):
    if noCheck:
        return True
    return canAccess(obj, 'title')

def canWriteObject(obj):
    return canWrite(obj, 'title')

def checkPermission(permission, obj):
    return baseCheckPermission(permission, obj)


def getCurrentPrincipal():
    interaction = getInteraction()
    if interaction is not None:
        parts = interaction.participations
        if parts:
            return parts[0].principal
    return None


# functions for setting security properties

def assignOwner(obj, principalId):
    prm = IPrincipalRoleManager(obj)
    prm.assignRoleToPrincipal('loops.Owner', principalId)

def removeOwner(obj, principalId):
    prm = IPrincipalRoleManager(obj)
    prm.removeRoleFromPrincipal('loops.Owner', principalId)


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

@component.adapter(ILoopsObject, IObjectCreatedEvent)
def setDefaultSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setDefaultRolePermissions()
    setter.setDefaultPrincipalRoles()


@component.adapter(IConcept, IAssignmentEvent)
def grantAcquiredSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setAcquiredRolePermissions(event.relation)
    setter.setAcquiredPrincipalRoles(event.relation)


@component.adapter(IConcept, IDeassignmentEvent)
def revokeAcquiredSecurity(obj, event):
    aObj = adapted(obj)
    setter = ISecuritySetter(aObj)
    setter.setAcquiredRolePermissions(event.relation, revert=True)
    setter.setAcquiredPrincipalRoles(event.relation, revert=True)
