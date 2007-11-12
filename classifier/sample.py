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
Sample classifier implementation.

$Id$
"""

from zope import component
from zope.app.catalog.interfaces import ICatalog
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.traversing.api import getName

from cybertools.organize.interfaces import IPerson
from cybertools.typology.interfaces import IType
from loops.classifier.base import Analyzer
from loops.classifier.base import Statement
from loops.common import adapted


class SampleAnalyzer(Analyzer):
    """ A fairly specific analyzer that expects filenames following this
        format:

          ctype_name_doctype_owner_date.extension

        with ctype = ('cust', 'emp'), spec is the short name of a customer or
        an employee, doctype = ('note', 'contract'), and owner
        being the short name of the user that is responsible for the
        resource.
    """

    def handleCustomer(self, name):
        custTypes = self.getTypes(('institution', 'customer',))
        for c in self.findConcepts(name):
            if IType(c).typeProvider in custTypes:
                yield Statement(c)

    def handleEmployee(self, name):
        for c in self.findConcepts(name):
            if IPerson.providedBy(adapted(c)):
                yield Statement(c)

    def handleOwner(self, name):
        cm = self.conceptManager
        ownedby = cm.get('ownedby')
        for c in self.findConcepts(name):
            if IPerson.providedBy(adapted(c)):
                yield Statement(c, ownedby)

    def handleDoctype(self, name):
        docTypes = self.getTypes(('doctype',))
        for c in self.findConcepts(name):
            if IType(c).typeProvider in docTypes:
                yield Statement(c)

    handlers = dict(cust=handleCustomer, emp=handleEmployee)

    def extractStatements(self, informationSet):
        result = []
        fn = informationSet.get('filename')
        if fn is None:
            return result
        parts = fn.split('_')
        if len(parts) > 1:
            ctype = parts.pop(0)
            if ctype in self.handlers:
                name = parts.pop(0)
                result.extend(self.handlers[ctype](self, name))
        if len(parts) > 1:
            result.extend(self.handleDoctype(parts.pop(0)))
        if len(parts) > 1:
            result.extend(self.handleOwner(parts.pop(0)))
        return result

    @Lazy
    def conceptManager(self):
        return self.context.context.getConceptManager()

    def getTypes(self, typeNames):
        cm = self.conceptManager
        return [c for c in [cm.get(name) for name in typeNames] if c is not None]
