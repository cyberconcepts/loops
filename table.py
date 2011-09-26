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

$Id$
"""

from BTrees.OOBTree import OOBTree
from zope import schema, component
from zope.interface import Interface, Attribute, implements
from zope.cachedescriptors.property import Lazy

from cybertools.composer.schema.grid.interfaces import Records
from loops.common import AdapterBase
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

    # better: specify column names (and possibly labels, types)
    # in Python code and reference by name here
    columns = schema.List(
        title=_(u'Columns'),
        description=_(u'The names of the columns of the data table. '
                      u'The first name is the name of the key column.'),
        value_type=schema.BytesLine(),
        default=['key', 'value'],
        required=True)

    data = Records(title=_(u'Table Data'),
        description=_(u'Table Data'),
        required=False)


class DataTable(AdapterBase):

    implements(IDataTable)

    _contextAttributes = list(IDataTable)
    _adapterAttributes = AdapterBase._adapterAttributes + ('columns', 'data')

    def getColumns(self):
        return getattr(self.context, '_columns', ['key', 'value'])
    def setColumns(self, value):
        self.context._columns = value
    columns = property(getColumns, setColumns)

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
