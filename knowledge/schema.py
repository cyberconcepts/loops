#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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

from cybertools.meta.interfaces import IOptions
from loops.knowledge.interfaces import IPerson
from loops.organize.schema import PersonSchemaFactory as BasePersonSchemaFactory


class PersonSchemaFactory(BasePersonSchemaFactory):

    adapts(IPerson)

    def __call__(self, interface, **kw):
        schema = super(PersonSchemaFactory, self).__call__(interface, **kw)
        if 'knowledge' in schema.fields.keys():
            kelements = IOptions(self.context.getLoopsRoot())('knowledge.element')
            if kelements:
                schema.fields['knowledge'].target_types = kelements
            else:
                del schema.fields['knowledge']
        return schema

