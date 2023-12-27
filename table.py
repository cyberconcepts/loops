#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
from zope.interface import implementer, implements, Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder, IIterableSource

from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.grid.interfaces import KeyTable, Records
from cybertools.composer.interfaces import IInstance
from loops.common import AdapterBase, adapted, baseObject
from loops.external.element import Element
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


class IRecordsTable(IDataTable):

    data = Records(title=_(u'Table Data'),
        description=_(u'Table Data'),
        required=False)


class DataTable(AdapterBase):

    implements(IDataTable)

    _contextAttributes = list(IDataTable)
    _adapterAttributes = AdapterBase._adapterAttributes + ('columns', 'data')

    def getColumns(self):
        cols = getattr(self.context, '_columns', None)
        if not cols:
            cols = getattr(baseObject(self.type), '_columns', None)
        return cols or ['key', 'value']
    def setColumns(self, value):
        self.context._columns = value
    columns = property(getColumns, setColumns)

    columnNames = columns

    def getData(self):
        data = getattr(self.context, '_data', None)
        if data is None:
            data = OOBTree()
            self.context._data = data
        reclen = len(self.columns) - 1
        for k, v in data.items():
            #v = v[:reclen]
            missing = reclen - len(v)
            if missing > 0:
                v += (missing * [u''])
                data[k] = v
        return data
    def setData(self, data):
        self.context._data = OOBTree(data)
    data = property(getData, setData)

    def dataAsRecords(self):
        return self.asRecords(self.data)

    def asRecords(self, data):
        result = []
        for k, v in sorted(data.items()):
            item = {}
            for idx, c in enumerate(self.columns):
                if idx == 0:
                    item[c] = k
                else:
                    item[c] = v[idx-1]
                    #item[c] = len(v) > idx and v[idx-1] or u''
            result.append(item)
        return result

    def getRowsByValue(self, column, value):
        return [r for r in self.dataAsRecords() if r[column] == value]


TypeInterfaceSourceList.typeInterfaces += (IDataTable,)


class DataTableSchemaFactory(SchemaFactory):

    adapts(IDataTable)

    def __call__(self, interface, **kw):
        schema = super(DataTableSchemaFactory, self).__call__(interface, **kw)
        if not isinstance(kw.get('manager'), Element):
            schema.fields.remove('columns')
            schema.fields.remove('viewName')
        return schema


def getRowValue(k, v):
    return v[0]

def getRowValueWithKey(k, v):
    return u' '.join((unicode(k), v[0]))


class DataTableSourceList(object):

    implements(IIterableSource)

    def __init__(self, context, valueProvider=getRowValue):
        self.context = context
        self.valueProvider = valueProvider

    def __iter__(self):
        items = [(k, self.valueProvider(k, v))
                    for k, v in self.context.data.items()]
        return iter(sorted(items, key=lambda x: x[1]))

    def __contains__(self, value):
        return value in self.context.data

    def __len__(self):
        return len(self.context.data)


class DataTableSourceListByValue(DataTableSourceList):

    def __iter__(self):
        items = [(k, v[0], v[1])
                    for k, v in self.context.data.items()]
        items.sort()
        return iter([(i[1], i[2]) for i in items])


class DataTableSourceBinder(object):

    implements(IContextSourceBinder)

    def __init__(self, tableName, valueProvider=getRowValue,
                 sourceList=None):
        self.tableName = tableName
        self.valueProvider = valueProvider
        self.sourceList = sourceList or DataTableSourceList

    def __call__(self, instance):
        if IInstance.providedBy(instance):
            context = instance.view.nodeView.context
        elif IConcept.providedBy(instance):
            context = baseObject(instance)
        else:
            context = baseObject(instance.context)
        dt = context.getLoopsRoot().getConceptManager()[self.tableName]
        return self.sourceList(adapted(dt), self.valueProvider)


@implementer(IRecordsTable)
class RecordsTable(DataTable):

    def getData(self):
        data = self.context._data
        if not isinstance(data, list):
            return self.asRecords(data)
        return data
    def setData(self, data):
        self.context._data = data
    data = property(getData, setData)

    def dataAsRecords(self):
        return self.data

