#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
Query management stuff.

$Id$
"""

from zope.app import zapi
from zope.component import adapts
from zope.interface import Interface, Attribute, implements
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import Lazy
from zope import schema
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.type import BaseType, TypeManager
from loops.interfaces import IConcept
from loops.common import AdapterBase
from loops.type import TypeInterfaceSourceList

_ = MessageFactory('loops')


class IQuery(Interface):
    """ The basic query interface.
    """

    def query(self, **kw):
        """ Execute the query and return a sequence of objects.
        """


class IQueryConcept(Interface):
    """ The schema for the query type.
    """

    viewName = schema.TextLine(
        title=_(u'Adapter/View name'),
        description=_(u'The name of the (multi-) adapter (typically a view) '
                       'to be used for the query and for presenting '
                       'the results'),
        default=u'',
        required=True)


class QueryConcept(AdapterBase):

    implements(IQueryConcept)

    _schemas = list(IQueryConcept) + list(IConcept)


TypeInterfaceSourceList.typeInterfaces += (IQueryConcept,)

