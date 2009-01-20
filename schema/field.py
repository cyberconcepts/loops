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
Field and field instance classes for grids.

$Id$
"""

from zope import component
from zope.component import adapts
from zope.interface import implements
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
import zope.schema

from cybertools.composer.schema.factory import createField
from cybertools.composer.schema.field import ListFieldInstance
from cybertools.composer.schema.interfaces import IField, IFieldInstance
from cybertools.composer.schema.interfaces import fieldTypes, undefined
from cybertools.util.format import toStr, toUnicode
from cybertools.util import json
from loops import util


relation_macros = ViewPageTemplateFile('relation_macros.pt')


class RelationSetFieldInstance(ListFieldInstance):

    def marshall(self, value):
        return [dict(title=v.title, uid=util.getUidForObject(v.context))
                for v in value]

    def display(self, value):
        return value

    def unmarshall(self, value):
        return value

    @Lazy
    def typesParams(self):
        result = []
        types = self.context.target_types
        for t in types:
            result.append('searchType=loops:concept:%s' % t)
        if result:
            return '?' + '&'.join(result)
        return ''
