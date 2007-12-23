#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
Automatic setup of a loops site for the constraint package.

$Id$
"""

from zope.component import adapts
from zope.interface import implements, Interface

from loops.concept import Concept
from loops.constraint.interfaces import IStaticConstraint
from loops.constraint.base import isPredicate, isType
from loops.constraint.base import hasConstraint, hasChildConstraint
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']
        # type concepts:
        constraint = self.addAndConfigureObject(concepts, Concept,
                            'staticconstraint', title=u'Constraint',
                            conceptType=type, typeInterface=IStaticConstraint)
        self.addObject(concepts, Concept, isPredicate,
                       title=u'is Predicate for Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, isType,
                       title=u'is Type for Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, hasConstraint,
                       title=u'has Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, hasChildConstraint,
                       title=u'has Child Constraint', conceptType=predicate)

