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
Interfaces for loops security management.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.util import _


class ISecuritySetter(Interface):

    def setDefaultSecurity():
        """ Set some default role permission assignments (grants) on the
            context object.
        """

    def setDefaultRolePermissions():
        """ Set some default role permission assignments (grants) on the
            context object.
        """

    def setDefaultPrincipalRoles():
        """ Assign default roles (e.g. owner) to certain principals
            (e.g. the user that created the object).
        """

    def acquireRolePermissions(revert=False):
        """ Check (immediate) parents's settings and set role permission
            assignments on the context object accordingly.
        """

    def setAcquiredSecurity(relation, revert=False, updated=None):
        """ Grant role permissions on children/resources for the relation given.

            If the ``revert`` argument is true unset the corresponding settings.
            Do not update objects in the ``updated`` collection if present.
        """

    def propagateSecurity(revert=False, updated=None):
        """ Update role permissions on all sub-objects according to the
            current setting of the context object.

            Ignore objects in the ``updated`` collection if present.
        """


class IWorkspaceInformation(Interface):
    """ Additional information belonging to a concept that controls
        security-related stuff for sub-objects.
    """

    propagateRolePermissions = Attribute('Whose role permissions should be '
                    'propagated to children (workspace_informaton or parent)?')

    propagateParentSecurity = Attribute('Should the security settings of '
                    'the workspace parent be propagated to children?')

