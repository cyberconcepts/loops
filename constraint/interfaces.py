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
Constraint definitions for restricting concepts and predicates available
for assignment as children or as concepts to resources.

Constraints may be used to build up an ontology, in the sense of a
ruleset that governs the possible relationships between objects.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.concept import Concept
from loops.interfaces import IConceptSchema
from loops.util import _


class IConstraint(Interface):
    """ A constraint is an adapter for concepts and resources and
        provides information on which relations are allowed for its
        client object.

        When the client object is a concept the constraint checks
        parent relations, if it is a resource it checks concept
        relations. In order to check for allowed child relations
        on a concept only you may specify a relation type of ``child``
        as an additional argument for the method calls.
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


class IStaticConstraint(IConceptSchema, IConstraint):
    """ Provides a statically assigned contstraint setting.

        Typically used as a concept adapter for a persistent constraint
        that allows editing of predicates, target types and cardinality
        of allowed relationships.
    """

    relationType = schema.Choice(
            title=_(u'Relation type'),
            description=_(u'Select the type of the relation for '
                    'which this constraint should be checked, '
                    '"default" meaning parent relations for concepts '
                    'and resource/concept relations for resources.'),
            values=('default', 'child'),
            default='default',
            required=True,)

    predicates = schema.List(
            title=_(u'Predicates'),
            description=_(u'Select the predicates that this '
                    'constraint should allow.'),
            value_type=schema.Choice(
                        title=_(u'Predicate'),
                        source='loops.predicateSource'),
            required=False,)

    types = schema.List(
            title=_(u'Target types'),
            description=_(u'Select the types of the objects '
                    'that this constraints should allow.'),
            value_type=schema.Choice(
                        title=_(u'Type'),
                        source='loops.conceptTypeSource'),
            required=False,)

    cardinality = schema.Choice(
            title=_(u'Cardinality'),
            description=_(u'Select an entry that represents the '
                    'allowed number of assigned items as specified '
                    'by this constraint.'),
            values=('0,*', '0,1', '1,*', '1,1'),
            default='0,*',
            required=True,)

