#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Constraint definitions for restricting concepts and predicates available
for assignment as children or as concepts to resources.

Constraints may be used to build up an ontology, in the sense of a
ruleset that governs the possible relationships between objects.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.util import _


class IConstraint(Interface):
    """ A constraint is an adapter for concepts and resources and
        provides information on which relations are allowed for its
        client object.

        When the client object is a concept the constraint checks
        for child relations, if it is a resource it checks for concept
        relations. In order to check for allowed parent relations (on
        a concept only) you may specify ``relationType=parent``
        on the method calls.
    """

    client = Attribute('Object that will be checked for allowed relations.')

    def isRelationAllowed(concept, predicate, relationType=None):
        """ Return True if this constraint allows the assignment of a
            relation to the client object specified by the target concept
            and the predicate given.
        """

    def getAllowedPredicates(relationType=None):
        """ Return a sequence of concepts of type ``predicate`` that
            may be used for assigning concepts to the client object.
        """


    def getAllowedConcepts(predicate, candidates=None, relationType=None):
        """ Return an iterable of concepts that - according to this
            constraint - may be assigned to the client object via the
            predicate given.

            If given, use candidates as a list of concepts from
            which to select the allowed targets.
        """


class IStaticConstraint(IConstraint):
    """ Provides a statically assigned contstraint setting.

        Typically used as a concept adapter for a persistent constraint
        that allows editing of predicates, target types and cardinality
        of allowed relationships.
    """

    relationType = schema.TextLine()

    predicates = schema.List()

    types = schema.List()

    cardinality = schema.List()

