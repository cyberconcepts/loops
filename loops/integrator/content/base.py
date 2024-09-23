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
Access to external objects.

$Id$
"""

import os, re

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements

from cybertools.integrator.interfaces import IContainerFactory
from loops.common import AdapterBase, adapted
from loops.integrator.content.interfaces import IExternalAccess
from loops.interfaces import IConcept
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IExternalAccess,)


class ExternalAccess(AdapterBase):
    """ A concept adapter for accessing external collection.
    """

    implements(IExternalAccess)
    adapts(IConcept)

    _contextAttributes = list(IExternalAccess) + list(IConcept)

    def __call__(self):
        factory = component.getUtility(IContainerFactory, self.providerName)
        address = os.path.join(self.baseAddress, self.address or '')
        return factory(address, __parent__=self.context)
