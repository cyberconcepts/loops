# loops.compound.blog.security

""" Security settings for blogs and blog posts.
"""

from zope.cachedescriptors.property import Lazy
from zope.component import adapts
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
