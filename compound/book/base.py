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
Implementation of book and book components
"""

from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.traversing.api import getName

from loops.compound.base import Compound
from loops.compound.book.interfaces import IPage
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IPage,)


class Page(Compound):

    implements(IPage)

    compoundPredicateNames = ['ispartof', 'standard']

    @Lazy
    def documentType(self):
        return self.context.getConceptManager()['documenttype']

    def getParts(self):
        result = {}
        for r in super(Page, self).getParts():
            for parent in r.getParents():
                if parent.conceptType == self.documentType:
                    item = result.setdefault(getName(parent), [])
                    item.append(r)
        return result
