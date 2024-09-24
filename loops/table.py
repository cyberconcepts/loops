"""Data (keyword-based) table definition and implementation.

Variant for tables without a key column: 
RecordsTable using a list of records (key-value pairs).
"""

from BTrees.OOBTree import OOBTree
from zope.cachedescriptors.property import Lazy
from zope import component, schema
from zope.component import adapts
from zope.interface import implementer, implementer, Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder, IIterableSource

from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.grid.interfaces import KeyTable, RecordsTable
from cybertools.composer.interfaces import IInstance
from cybertools.meta.interfaces import IOptions
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

    data = RecordsTable(title=_(u'Table Data'),
        description=_(u'Table Data'),
        required=False)


@implementer(IDataTable)
class DataTable(AdapterBase):


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


TypeInterfaceSourceList.typeInterfaces += (IDataTable, IRecordsTable)


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


@implementer(IIterableSource)
class DataTableSourceList(object):

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


@implementer(IContextSourceBinder)
class DataTableSourceBinder(object):

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
            data = self.asRecords(data)
        sortcrit = IOptions(self.type)('table.sort')
        if sortcrit:
            data.sort(key=lambda x: [x.get(f) for f in sortcrit])
        return data
    def setData(self, data):
        self.context._data = data
    data = property(getData, setData)

    def dataAsRecords(self):
        return self.data

