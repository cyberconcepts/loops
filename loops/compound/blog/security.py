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
Security settings for blogs and blog posts.
"""

from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope.traversing.api import getName

from loops.compound.blog.interfaces import IBlogPost
from loops.security.common import allowEditingForOwner, assignOwner, restrictView
from loops.security.common import getCurrentPrincipal
from loops.security.setter import LoopsObjectSecuritySetter


class BlogPostSecuritySetter(LoopsObjectSecuritySetter):

    adapts(IBlogPost)

    def setDefaultRolePermissions(self):
        allowEditingForOwner(self.context.context)

    def setDefaultPrincipalRoles(self):
        assignOwner(self.context.context, self.principalId)

    def setAcquiredSecurity(self, relation, revert=False):
        #if self.isAcquiring(relation.predicate):
        if relation.predicate in self.acquiringPredicates:
            allowEditingForOwner(relation.second, revert=revert)
            if self.context.private:
                restrictView(relation.second, revert=revert)
            if revert:
                removeOwner(relation.second, self.principalId)
            else:
                assignOwner(relation.second, self.principalId)

    @Lazy
    def acquiringPredicates(self):
        names = ('ispartof',)
        return [self.conceptManager.get(n) for n in names]

    @Lazy
    def principalId(self):
        return getCurrentPrincipal().id


def isAcquiring(predicate):
    # TODO: use a predicate option for this.
    return getName(predicate) in ('ispartof',)
