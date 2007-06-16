#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Adapters and others classes for analyzing resources.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.event import notify
from zope.interface import implements
from zope.traversing.api import getName, getParent

from loops.classifier.interfaces import IClassifier
from loops.common import AdapterBase, adapted
from loops.interfaces import IResource, IConcept
from loops.resource import Resource
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IClassifier,)


class Classifier(AdapterBase):
    """ A concept adapter for analyzing resources.
    """

    implements(IClassifier)
    adapts(IConcept)

    _adapterAttributes = ('context', '__parent__',)
    _contextAttributes = list(IClassifier) + list(IConcept)

