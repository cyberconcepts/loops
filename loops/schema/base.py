# loops.schema.base

""" Specialized field definitions.
"""

from zope.component import adapts
from zope.interface import Attribute, implementer
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


@implementer(IRelation)
class Relation(Field):

    __typeInfo__ = ('relation',
                    FieldType('relation', 'relation',
                              u'A field representing a related object.',
                              instanceName='relation',
                              displayRenderer='display_relation'))

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types', ())
        super(Relation, self).__init__(*args, **kw)


@implementer(IRelationSet)
class RelationSet(List):

    __typeInfo__ = ('relationset',
                    FieldType('relationset', 'relationset',
                              u'A field representing a sequence of related objects.',
                              instanceName='relationset',
                              displayRenderer='display_relationset'))

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types', ())
        self.selection_view = kw.pop('selection_view', None)
        super(RelationSet, self).__init__(*args, **kw)

