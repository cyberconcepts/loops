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
Predicate management.

$Id$
"""

from zope import component, schema
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName

from loops.interfaces import ILoopsObject, IConcept, IResource
from loops.interfaces import IPredicate
from loops.concept import Concept
from loops.common import AdapterBase
from loops.type import TypeInterfaceSourceList as BaseTypeInterfaceSourceList


BaseTypeInterfaceSourceList.typeInterfaces += (IPredicate,)


class Predicate(AdapterBase):
    """ typeInterface adapter for concepts of type 'predicate'.
    """

    implements(IPredicate)

    _contextAttributes = list(IPredicate) + list(IConcept)


class TypeInterfaceSourceList(BaseTypeInterfaceSourceList):
    """ Collects type interfaces for predicates, i.e. interfaces that
        may be used for specifying additional attributes of relations.
    """

    typeInterfaces = ()

