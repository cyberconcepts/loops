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
Security-related views.

$Id$
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope import component
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy

from loops.security.common import WorkspaceInformation
from loops.security.perm import PermissionView


permission_template = ViewPageTemplateFile('manage_permissionform.pt')


class ManageWorkspaceView(PermissionView):
    """ View for managing workspace information.
    """

    def __init__(self, context, request):
        context = removeSecurityProxy(context)
        wi = context.workspaceInformation
        if wi is None:
            wi = context.workspaceInformation = WorkspaceInformation(context)
        PermissionView.__init__(self, wi, request)

    @Lazy
    def permission_macros(self):
        return permission_template.macros
