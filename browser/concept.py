#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
Definition of the Task view class.

$Id$
"""

from zope.app import zapi
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope import schema
from zope.security.proxy import removeSecurityProxy
from loops.browser.common import BaseView
from loops.browser.terms import LoopsTerms


class ConceptView(BaseView):

    def children(self):
        request = self.request
        for c in self.context.getChildren():
            yield ConceptView(c, request)

    def parents(self):
        request = self.request
        for c in self.context.getParents():
            yield ConceptView(c, request)

    def update(self):
        concept_name = self.request.get('concept_name', None)
        if concept_name:
            concept = zapi.getParent(self.context)[concept_name]
            self.context.assignChild(removeSecurityProxy(concept))
        return True

    def getVocabularyForRelated(self):
        source = ConceptSourceList(self.context)
        for candidate in source:
            yield LoopsTerms(ConceptView(candidate, self.request), self.request)


class ConceptSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)
        root = self.context.getLoopsRoot()
        self.concepts = root.getConceptManager()

    def __iter__(self):
        for obj in self.concepts.values():
            yield obj

    def __len__(self):
        return len(self.concepts)

