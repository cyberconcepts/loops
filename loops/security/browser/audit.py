#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
End user views for security audits and similar tasks.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.securitypolicy.interfaces import IRolePermissionMap
from zope.securitypolicy.zopepolicy import SettingAsBoolean
from zope.traversing.api import getName, getParent

from loops.browser.concept import ConceptView
from loops import util
from loops.util import _


class BaseSecurityView(ConceptView):

    template = ViewPageTemplateFile('audit.pt')


class RolePermissionsByType(BaseSecurityView):

    @Lazy
    def macro(self):
        return self.template.macros['role_permissions']

    @Lazy
    def types(self):
        result = [self.conceptManager.get(name) for name in self.options('types')]
        return [dict(token=getName(t), label=t.title, object=t)
                        for t in result if t is not None]

    @Lazy
    def selectedType(self):
        if 'selected_type' in self.request.form:
            typeName = self.request.form['selected_type']
            type = self.conceptManager.get(typeName)
            return dict(token=getName(type), label=type.title, object=type)
        if self.types:
            return self.types[0]
        return dict(token=u'', label=u'', object=None)

    @Lazy
    def objects(self):
        if not self.selectedType:
            return []
        result = self.selectedType['object'].getChildren([self.typePredicate])
        return [dict(title=o.title, object=o,
                     settings=self.getPermissionSettings(o),)
                        for o in result]

    def getPermissionSettings(self, obj):
        result = []
        rpm = IRolePermissionMap(obj, None)
        for r in self.roles:
            if rpm is not None:
                setting = rpm.getSetting(self.selectedPermission, r)
                setting = SettingAsBoolean[setting]
                if setting is not None:
                    result.append(setting and '+' or '-')
                else:
                    result.append(u'')
            else:
                result.append(u'')
        return result

    @Lazy
    def permissions(self):
        return self.options('permissions')

    @Lazy
    def selectedPermission(self):
        if 'selected_permission' in self.request.form:
            return self.request.form['selected_permission']
        if self.permissions:
            return self.permissions[0]
        return u''

    @Lazy
    def roles(self):
        return self.options('roles')


class WorkspaceAssignments(BaseSecurityView):

    @Lazy
    def macro(self):
        return self.template.macros['workspace_assignments']

    @Lazy
    def workspacePredicates(self):
        result = [self.conceptManager.get(p)
                    for p in ('isowner', 'ismaster', 'ismember')]
        return [p for p in result if p is not None]

    @Lazy
    def workspaces(self):
        typeNames = self.options('workspace')
        if typeNames:
            type = self.conceptManager.get(typeNames[0])
            return type.getChildren([self.typePredicate])
        return []

    def getAssignments(self, workspace):
        rels = []
        for wsp in self.workspacePredicates:
            rels.append(workspace.getChildRelations([wsp]))
        return rels


class PersonWorkspaceAssignments(WorkspaceAssignments):

    @Lazy
    def macro(self):
        return self.template.macros['person_workspace_assignments']

    @Lazy
    def persons(self):
        tPerson = self.conceptManager['person']
        return tPerson.getChildren([self.typePredicate])

    def getAssignments(self, person):
        rels = []
        for ws in self.workspaces:
            rels.append(ws.getChildRelations(self.workspacePredicates, person))
        return [', '.join([r.predicate.title for r in prels]) for prels in rels]
