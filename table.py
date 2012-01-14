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
Data (keyword-based) table definition and implementation.
"""

from BTrees.OOBTree import OOBTree
from zope.cachedescriptors.property import Lazy
from zope import component, schema
from zope.component import adapts
from zope.interface import implements, Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder, IIterableSource

from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.grid.interfaces import KeyTable
from loops.common import AdapterBase, adapted, baseObject
from loops.interfaces import IConcept, IConceptSchema, ILoopsAdapter
from loops.type import TypeInterfaceSourceList
from loops import util
from loops.util import _


class IDataTable(IConceptSchema, ILoopsAdapter):
    """ The schema for the data table type.
    """

    viewName = schema.TextLine(
        title=_(u'Adapter/View name'),
        description=_(u'Optional name of the view '
                      u'to be used for presenting '
                      u'the data of the table.'),
        default=u'',
        required=False)

    columns = schema.List(
        title=_(u'Columns'),
        description=_(u'The names of the columns of the data table. '
                      u'The first name is the name of the key column.'),
        value_type=schema.BytesLine(),
        default=['key', 'value'],
        required=True)

    data = KeyTable(title=_(u'Table Data'),
        description=_(u'Table Data'),
        required=False)

IDataTable['columns'].hidden = True


class DataTable(AdapterBase):

    implements(IDataTable)

    _contextAttributes = list(IDataTable)
    _adapterAttributes = AdapterBase._adapterAttributes + ('columns', 'data')

    def getColumns(self):
        return getattr(self.context, '_columns', ['key', 'value'])
    def setColumns(self, value):
        self.context._columns = value
    columns = property(getColumns, setColumns)

    columnNames = columns

    def getData(self):
        data = getattr(self.context, '_data', None)
        if data is None:
            data = OOBTree()
            self.context._data = data
        return data
    def setData(self, data):
        self.context._data = OOBTree(data)
    data = property(getData, setData)


TypeInterfaceSourceList.typeInterfaces += (IDataTable,)


class DataTableSchemaFactory(SchemaFactory):

    adapts(IDataTable)

    def __call__(self, interface, **kw):
        schema = super(DataTableSchemaFactory, self).__call__(interface, **kw)
        schema.fields.remove('columns')
        schema.fields.remove('viewName')
        return schema


class DataTableSourceBinder(object):

    implements(IContextSourceBinder)

    def __init__(self, tableName):
        self.tableName = tableName

    def __call__(self, instance):
        #context = baseObject(instance.context)
        context = instance.view.nodeView.context
        dt = context.getLoopsRoot().getConceptManager()[self.tableName]
        return DataTableSourceList(adapted(dt))


class DataTableSourceList(object):

    implements(IIterableSource)

    def __init__(self, context):
        self.context = context

    def __iter__(self):
        items = [(k, v[0]) for k, v in self.context.data.items()]
        return iter(sorted(items, key=lambda x: x[1]))

    def __len__(self):
        return len(self.context.data)
