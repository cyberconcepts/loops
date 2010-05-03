#
#  Copyright (c) 2005 Helmut Merz helmutm@cy55.de
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
Specialized schema factories

$Id$
"""

from zope.component import adapts

from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.field import FieldInstance
from cybertools.composer.schema.interfaces import FieldType
from cybertools.organize.interfaces import SimpleList
from loops.organize.interfaces import IPerson, UserId


class PersonSchemaFactory(SchemaFactory):

    adapts(IPerson)

    def __call__(self, interface, **kw):
        schema = super(PersonSchemaFactory, self).__call__(interface, **kw)
        #if 'phoneNumbers' in schema.fields.keys():
        #    schema.fields.phoneNumbers.instance_name ='simplelist'
        if 'birthDate' in schema.fields.keys():
            schema.fields.birthDate.display_format = ('date', 'long')
        del schema.fields['userId']
        return schema


class SimpleListFieldInstance(FieldInstance):

    def display(self, value):
        if not value:
            return ''
        return ' | '.join(value)
