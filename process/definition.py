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
Adapters for IConcept providing interfaces from the
cybertools.knowledge package.

$Id$
"""

from zope import interface, component
from zope.app import zapi
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from cybertools.process.interfaces import IProcess
from cybertools.process.definition import Process as BaseProcess
from loops.interfaces import IConcept
from loops.type import TypeInterfaceSourceList, AdapterBase


# register type interfaces - (TODO: use a function for this)

TypeInterfaceSourceList.typeInterfaces += (IProcess,)


class ProcessAdapterMixin(object):

    @Lazy
    def conceptManager(self):
        return self.context.getLoopsRoot().getConceptManager()

    @Lazy
    def successorPred(self):
        return self.conceptManager['follows']


class Process(AdapterBase, BaseProcess, ProcessAdapterMixin):
    """ A typeInterface adapter for concepts of type 'process'.
    """

    implements(IProcess)

