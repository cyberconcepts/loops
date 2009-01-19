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
Specialized fields and schema factories

$Id$
"""

from zope.component import adapts
from zope.interface import Attribute, implements
from zope.schema import Choice, List
from zope.schema.interfaces import IChoice, IList

from cybertools.composer.schema.factory import SchemaFactory
from loops.interfaces import IResourceAdapter, IFile, INote

# fields

class IRelation(IChoice):
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


class Relation(Choice):

    implements(IRelation)

    __typeInfo = ('relation',)

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types')
        super(Relation, self).__init__(*args, **kw)


class RelationSet(List):

    implements(IRelationSet)

    __typeInfo = ('relationset',)

    def __init__(self, *args, **kw):
        self.target_types = kw.pop('target_types')
        super(RelationSet, self).__init__(*args, **kw)


# schema factories

class ResourceSchemaFactory(SchemaFactory):

    adapts(IResourceAdapter)

    def __call__(self, interface, **kw):
        schema = super(ResourceSchemaFactory, self).__call__(interface, **kw)
        #if 'data' in schema.fields.keys():
        schema.fields.data.height = 10
        if self.context.contentType == 'text/html':
            schema.fields.data.fieldType = 'html'
        return schema


class FileSchemaFactory(SchemaFactory):

    adapts(IFile)

    def __call__(self, interface, **kw):
        schema = super(FileSchemaFactory, self).__call__(interface, **kw)
        if 'request' in kw:
            principal = kw['request'].principal
            if not principal or principal.id != 'rootadmin':
                schema.fields.remove('contentType')
        return schema


class NoteSchemaFactory(SchemaFactory):

    adapts(INote)

    def __call__(self, interface, **kw):
        schema = super(NoteSchemaFactory, self).__call__(interface, **kw)
        schema.fields.remove('description')
        schema.fields.data.height = 5
        return schema

