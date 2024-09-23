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
Automatic setup of a loops site for the process package.

$Id$
"""

from zope.component import adapts
from zope.interface import implements, Interface

from cybertools.process.interfaces import IProcess
from loops.concept import Concept
from loops.interfaces import ITypeConcept
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']
        # type concepts:
        process = self.addObject(concepts, Concept, 'process', title=u'Process',
                                 conceptType=type)
        processTypeAdapter = ITypeConcept(process)
        if not processTypeAdapter.typeInterface:
            processTypeAdapter.typeInterface = IProcess
        # predicates:
        follows = self.addObject(concepts, Concept, 'follows', title=u'follows',
                        conceptType=predicate)


