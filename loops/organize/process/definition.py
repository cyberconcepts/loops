# loops.organize.process.definition

""" Adapters for IConcept providing interfaces from the
cybertools.knowledge package.
"""

from zope import interface, component
from zope.component import adapts
from zope.interface import implementer
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
#from cybertools.process.interfaces import IProcess
from cybertools.process.definition import Process as BaseProcess
from loops.interfaces import IConcept
from loops.common import AdapterBase
from loops.organize.process.interfaces import IProcess
from loops.type import TypeInterfaceSourceList


# register type interfaces - (TODO: use a function for this)

TypeInterfaceSourceList.typeInterfaces += (IProcess,)


class ProcessAdapterMixin(object):

    @Lazy
    def conceptManager(self):
        return self.context.getLoopsRoot().getConceptManager()

    @Lazy
    def successorPred(self):
        return self.conceptManager['follows']


@implementer(IProcess)
class Process(AdapterBase, BaseProcess, ProcessAdapterMixin):
    """ A typeInterface adapter for concepts of type 'process'.
    """

    pass

