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
Specialized field definitions.

$Id$
"""

from zope.component import adapts
from zope.interface import Attribute, implements
from zope.schema import Field, List
from zope.schema.interfaces import IField, IList

from cybertools.composer.schema.interfaces import FieldType


class IRelation(IField):
    """ An object addressed via a single relation.
    """

    target_types = Attribute('A list of names that denote types of '
                'loops objects (typically concept types) that may be used as '
                'targets for the relation.')


class IRelationSet(IList):
    """ A collection of objects addressed via a set of relations.

        Despite its name, the collection may have a predefined order.
    """

    target_types = Attribute('A list of names that denote types of '
                'loops objects (typically concept types) that may be used as '
                'targets for the relations.')
    selection_view = Attribute('The name of a view that provides a collection '
                'of candidates to select from, in JSON format.')


class Relation(Field):

    implements(IRelation)

    __typeInfo__ = ('relation',
                    FieldType('relation', 'relation',
                              u'A field representing a related object.',
                              instanceName='relation'))

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types', ())
        super(Relation, self).__init__(*args, **kw)


class RelationSet(List):

    implements(IRelationSet)

    __typeInfo__ = ('relationset',
                    FieldType('relationset', 'relationset',
                              u'A field representing a sequence of related objects.',
                              instanceName='relationset',
                              displayRenderer='display_relationset'))

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types', ())
        self.selection_view = kw.pop('selection_view', None)
        super(RelationSet, self).__init__(*args, **kw)

