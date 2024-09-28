# loops.integrator.content.base

""" Access to external objects.
"""

import os, re

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implementer

from cybertools.integrator.interfaces import IContainerFactory
from loops.common import AdapterBase, adapted
from loops.integrator.content.interfaces import IExternalAccess
from loops.interfaces import IConcept
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IExternalAccess,)


@implementer(IExternalAccess)
class ExternalAccess(AdapterBase):
    """ A concept adapter for accessing external collection.
    """

    adapts(IConcept)

    _contextAttributes = list(IExternalAccess) + list(IConcept)

    def __call__(self):
        factory = component.getUtility(IContainerFactory, self.providerName)
        address = os.path.join(self.baseAddress, self.address or '')
        return factory(address, __parent__=self.context)
