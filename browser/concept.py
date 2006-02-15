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
from zope.app.catalog.interfaces import ICatalog
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.app.form.browser.interfaces import ITerms
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.publisher.interfaces import BadRequest
from zope import schema
from zope.security.proxy import removeSecurityProxy
from loops.concept import Concept
from loops.browser.common import BaseView, LoopsTerms


class ConceptView(BaseView):

    def children(self):
        ch = self.context.getChildren()
        return ch and self.viewIterator(ch) or []

    def parents(self):
        p = self.context.getParents()
        return p and self.viewIterator(p) or []

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            yield ConceptView(o, request)

    def update(self):
        action = self.request.get('action')
        if action is None:
            return True
        if action == 'create':
            self.createAndAssign()
            return True
        tokens = self.request.get('tokens', [])
        for token in tokens:
            concept = self.loopsRoot.loopsTraverse(token)
            if action == 'assign':
                assignAs = self.request.get('assignAs', 'child')
                if assignAs == 'child':
                    self.context.assignChild(removeSecurityProxy(concept))
                elif assignAs == 'parent':
                    self.context.assignParent(removeSecurityProxy(concept))
                else:
                    raise(BadRequest, 'Illegal assignAs parameter: %s.' % assignAs)
            elif action == 'remove':
                qualifier = self.request.get('qualifier')
                if qualifier == 'parents':
                    self.context.deassignParents(concept)
                elif qualifier == 'children':
                    self.context.deassignChildren(concept)
                else:
                    raise(BadRequest, 'Illegal qualifier: %s.' % qualifier)
            else:
                    raise(BadRequest, 'Illegal action: %s.' % action)
        return True

    def createAndAssign(self):
        request = self.request
        name = request.get('create.name')
        if not name:
            raise(BadRequest, 'Empty name.')
        title = request.get('create.title', u'')
        type = request.get('create.type')
        concept = Concept(title)
        container = self.loopsRoot.getConceptManager()
        container[name] = concept
        assignAs = self.request.get('assignAs', 'child')
        if assignAs == 'child':
            self.context.assignChild(removeSecurityProxy(concept))
        elif assignAs == 'parent':
            self.context.assignParent(removeSecurityProxy(concept))
        else:
            raise(BadRequest, 'Illegal assignAs parameter: %s.' % assignAs)

    #def getVocabularyForRelated(self):  # obsolete
    #    source = ConceptSourceList(self.context)
    #    terms = zapi.getMultiAdapter((source, self.request), ITerms)
    #    for candidate in source:
    #        yield terms.getTerm(candidate)

    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        if searchTerm:
            cat = zapi.getUtility(ICatalog)
            result = cat.searchResults(loops_searchableText=searchTerm)
        else:
            result = self.loopsRoot.getConceptManager().values()
        return self.viewIterator(result)

