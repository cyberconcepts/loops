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
Base classes for security setters, i.e. adapters that provide standardized
methods for setting role permissions and other security-related stuff.

$Id$
"""

from zope import component
from zope.component import adapts
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, Interface

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

    def setAcquiredRolePermissions(self, relation, revert=False):
        pass

    def setAcquiredPrincipalRoles(self, relation, revert=False):
        pass
