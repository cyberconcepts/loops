#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Security-related views.

$Id$
"""

from zope.app.authentication.groupfolder import GroupInformation
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IPermission
from zope.app.security.settings import Allow, Deny, Unset
from zope.app.securitypolicy.browser import granting
from zope.app.securitypolicy.browser.rolepermissionview import RolePermissionView
from zope import component
from zope.event import notify
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.security.proxy import removeSecurityProxy
from zope.securitypolicy.interfaces import IPrincipalRoleManager, \
                                               IRolePermissionMap
from zope.securitypolicy.interfaces import IPrincipalPermissionManager, \
                                               IPrincipalPermissionMap
from zope.securitypolicy.zopepolicy import SettingAsBoolean
from zope.traversing.api import getName, getParent, getParents

from loops.common import adapted
from loops.organize.util import getGroupsFolder
from loops.security.common import WorkspaceInformation
from loops.security.common import localPermissions, localRoles, setPrincipalRole
from loops.security.interfaces import ISecuritySetter


permission_template = ViewPageTemplateFile('manage_permissionform.pt')


class Granting(granting.Granting):

    def status(self):
        value = super(Granting, self).status()
        if value:
            setter = ISecuritySetter(adapted(self.context))
            setter.propagateSecurity()
        return value


class PermissionView(object):
    """ View for permission editing.
    """

    def __init__(self, context, request):
        self.context = context
        # make sure the real view (delegate) updates our context when
        # talking about the context's parent:
        self.__parent__ = context
        self.request = request
        self.delegate = RolePermissionView()
        self.delegate.context = self
        self.delegate.request = request
        self.permissionId = request.get('permission_to_manage') or 'zope.View'

    def pagetip(self):
        return self.delegate.pagetip()

    def roles(self):
        return self.delegate.roles()

    def permissions(self):
        return self.delegate.permissions()

    def availableSettings(self, noacquire=False):
        return self.delegate.availableSettings(noacquire)

    def permissionRoles(self):
        return self.delegate.permissionRoles()

    def permissionForID(self, pid):
        return self.delegate.permissionForID(pid)

    @Lazy
    def permission(self):
        return self.permissionForID(self.permissionId)

    def roleForID(self, rid):
         return self.delegate.roleForID(rid)

    def update(self, testing=None):
        value = self.delegate.update(testing)
        if value:
            setter = ISecuritySetter(self.adapted)
            setter.propagateSecurity()
        return value

    @Lazy
    def adapted(self):
        return adapted(self.context)

    def getAcquiredPermissionSetting(self, role, perm):
        for obj in getParents(self.context):
            rpm = IRolePermissionMap(obj, None)
            if rpm is not None:
                setting = rpm.getSetting(perm, role)
                setting = SettingAsBoolean[setting]
                if setting is not None:
                    return setting and '+' or '-'
        return ''

    def listUsersForRole(self, rid):
        result = ''
        direct = IPrincipalRoleManager(self.context).getPrincipalsForRole(rid)
        if direct:
            result = '<strong>' + self.renderEntry(direct) + '</strong>'
        acquired = []
        for obj in getParents(self.context):
            prm = IPrincipalRoleManager(obj, None)
            if prm is not None:
                entry = prm.getPrincipalsForRole(rid)
                if entry:
                    acquired.append(self.renderEntry(entry))
        if acquired:
            if result:
                result += '<br />'
            result += '<br />'.join(acquired)
        return result

    def renderEntry(self, entry):
        result = []
        for e in entry:
            value = SettingAsBoolean[e[1]]
            value = (value is False and '-') or (value and '+') or ''
            result.append(value + e[0])
        return ', '.join(result)

    def getPrincipalPermissions(self):
        result = ''
        ppm = IPrincipalPermissionMap(self.context)
        direct = ppm.getPrincipalsForPermission(self.permissionId)
        if direct:
            result = '<strong>' + self.renderEntry(direct) + '</strong>'
        acquired = []
        for obj in getParents(self.context):
            ppm = IPrincipalPermissionMap(obj, None)
            if ppm is not None:
                entry = ppm.getPrincipalsForPermission(self.permissionId)
                if entry:
                    acquired.append(self.renderEntry(entry))
        if acquired:
            if result:
                result += '<br />'
            result += '<br />'.join(acquired)
        return result

    def getPermissions(self):
        return sorted(name for name, perm in component.getUtilitiesFor(IPermission)
                           if name in localPermissions)

    def hideRole(self, role):
        return role not in localRoles


class ManageWorkspaceView(PermissionView):
    """ View for managing workspace information.
    """

    def __init__(self, context, request):
        context = removeSecurityProxy(context)
        wi = context.workspaceInformation
        if wi is None:
            wi = context.workspaceInformation = WorkspaceInformation(context)
        PermissionView.__init__(self, wi, request)

    def update(self, testing=None):
        if 'SUBMIT_PERMS' in self.request.form:
            super(ManageWorkspaceView, self).update(testing)
        elif 'save_wsinfo'  in self.request.form:
            self.saveWSInfo()

    def saveWSInfo(self):
        gn = {}
        form = self.request.form
        gfName = self.context.workspaceGroupsFolderName
        gf = getGroupsFolder(self.context, gfName, create=True)
        parentRM = IPrincipalRoleManager(self.parent)
        wsiRM = IPrincipalRoleManager(self.context)
        for pn in form.get('predicate_name', []):
            groupName = form.get('group_name_' + pn)
            gn[pn] = groupName
            if groupName and groupName not in gf:
                group = GroupInformation(groupName)
                notify(ObjectCreatedEvent(group))
                gf[groupName] = group
                notify(ObjectModifiedEvent(group))
            roleParent = bool(form.get('role_parent_' + pn))
            roleWSI = bool(form.get('role_wsi_' + pn))
            roleName = 'loops.' + pn.lstrip('is').title()
            gid = '.'.join((gfName, groupName))
            setPrincipalRole(parentRM, roleName, gid,
                             roleParent and Allow or None)
            setPrincipalRole(wsiRM, roleName, gid,
                             roleWSI and Allow or None)
        self.context.workspaceGroupNames = gn
        setter = ISecuritySetter(adapted(self.parent))
        setter.propagateSecurity()
        #setter = ISecuritySetter(adapted(self.context))
        #setter.propagateSecurity()

    @Lazy
    def permission_macros(self):
        return permission_template.macros

    @Lazy
    def parent(self):
        return self.context.getParent()

    @Lazy
    def adapted(self):
        return adapted(self.parent)

    def getGroupsInfo(self):
        root = self.parent.getLoopsRoot()
        conceptManager = root.getConceptManager()
        def getDefaultGroupName(predicateName):
            rootName = '_'.join([getName(obj) for obj in
                            reversed(getParents(conceptManager)[:-1])])
            objName = getName(self.parent)
            return '.'.join((rootName, objName, predicateName.lstrip('is')))
        apn = [pn for pn in self.context.allocationPredicateNames
                  if pn in conceptManager]
        gn = self.context.workspaceGroupNames
        if not isinstance(gn, dict):    # backwards compatibility
            gn = {}
        result = [dict(predicateName=pn,
                       predicateTitle=conceptManager[pn].title,
                       groupName=None, groupExists=False,
                       roleParent=False, roleWSI=False)
                    for pn in apn]
        gfName = self.context.workspaceGroupsFolderName
        gf = getGroupsFolder(self.context, gfName)
        #if gf is None:
        #    return result
        parentRMget = IPrincipalRoleManager(self.parent).getPrincipalsForRole
        wsiRMget = IPrincipalRoleManager(self.context).getPrincipalsForRole
        for item in result:
            pn = item['predicateName']
            groupName = gn.get(pn)
            if groupName is None:
                groupName = getDefaultGroupName(pn)
            item['groupName'] = groupName
            roleName = 'loops.' + pn.lstrip('is').title()
            if gf is not None and groupName in gf:
                item['groupExists'] = True
            gid = '.'.join((gfName, groupName))
            item['roleParent'] = isSet(parentRMget(roleName), gid)
            item['roleWSI'] = isSet(wsiRMget(roleName), gid)
        return result


def isSet(entry, id):
    for name, setting in entry:
        if name == id:
            return SettingAsBoolean[setting]
