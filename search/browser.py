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
Definition of basic view classes and other browser related stuff for the
loops.search package.

$Id$
"""

from zope.app import zapi
from zope import interface, component
from zope.app.catalog.interfaces import ICatalog
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.namedtemplate import NamedTemplate, NamedTemplateImplementation
from zope.i18nmessageid import MessageFactory

from cybertools.ajax import innerHtml
from cybertools.typology.interfaces import ITypeManager
from loops.browser.common import BaseView
from loops import util
from loops.util import _


template = ViewPageTemplateFile('search.pt')


class Search(BaseView):

    maxRowNum = 0

    template = template

    @Lazy
    def macro(self):
        return template.macros['search']

    @Lazy
    def catalog(self):
        return component.getUtility(ICatalog)

    @property
    def rowNum(self):
        """ Return the rowNum to be used for identifying the current search
            parameter row.
        """
        n = self.request.get('loops.rowNum', 0)
        if n: # if given directly we don't use the calculation
            return n
        n = (self.maxRowNum or self.request.get('loops.maxRowNum', 0)) + 1
        self.maxRowNum = n
        return n

    def conceptTypesForSearch(self):
        general = [('loops:concept:*', 'Any Concept'),]
        return util.KeywordVocabulary(general + sorted([(t.tokenForSearch, t.title)
                        for t in ITypeManager(self.context).types
                            if 'concept' in t.qualifiers]))

    def initDojo(self):
        self.registerDojo()
        cm = self.controller.macros
        jsCall = 'dojo.require("dojo.widget.ComboBox")'
        cm.register('js-execute', jsCall, jsCall=jsCall)

    def listConcepts(self):
        """ Used for dojo.widget.ComboBox.
        """
        request = self.request
        request.response.setHeader('Content-Type', 'text/plain; charset=UTF-8')
        text = request.get('searchString', '')
        type = request.get('searchType') or 'loops:concept:*'
        if type.endswith('*'):
            start = type[:-1]
            end = start + '\x7f'
        else:
            start = end = type
        cat = self.catalog
        if text:
            result = cat.searchResults(loops_type=(start, end), loops_text=text+'*')
        else:
            result = cat.searchResults(loops_type=(start, end))
        return str(sorted([[`o.title`[2:-1], `zapi.getName(o)`[2:-1]]
                        for o in result])).replace('\\\\x', '\\x')

    def submitReplacing(self, targetId, formId, view):
        self.registerDojo()
        return 'return submitReplacing("%s", "%s", "%s")' % (
                    targetId, formId,
                    '%s/.target%s/@@searchresults.html' % (view.url, self.uniqueId))


class SearchResults(BaseView):
    """ Provides results as inner HTML """

    @Lazy
    def macro(self):
        return template.macros['search_results']

    def __call__(self):
        return innerHtml(self)

    @Lazy
    def catalog(self):
        return component.getUtility(ICatalog)

    @Lazy
    def results(self):
        result = set()
        request = self.request
        r3 = self.queryConcepts()
        type = request.get('search.1.text', 'loops:*')
        text = request.get('search.2.text')
        if not r3 and not text and '*' in type: # there should be some sort of selection...
            return result
        #if r3 and type != 'loops:*':
        #    typeName = type.split(':')[-1]
        #    r3 = set(o for o in r3 if self.isType(o, typeName))
        #if text or not '*' in loops:
        if text or type != 'loops:*':  # TODO: this may be highly inefficient! see above
            useTitle = request.get('search.2.title')
            useFull = request.get('search.2.full')
            r1 = set()
            cat = self.catalog
            if useFull and text and not type.startswith('loops:concept:'):
                criteria = {'loops_resource_textng': {'query': text},}
                r1 = set(cat.searchResults(**criteria))
            if type.endswith('*'):
                start = type[:-1]
                end = start + '\x7f'
            else:
                start = end = type
            criteria = {'loops_type': (start, end),}
            if useTitle and text:
                criteria['loops_title'] = text
            r2 = set(cat.searchResults(**criteria))
            result = r1.union(r2)
            result = set(r for r in result if r.getLoopsRoot() == self.loopsRoot)
        if r3 is not None:
            if result:
                result = result.intersection(r3)
            else:
                result = r3
        result = sorted(result, key=lambda x: x.title.lower())
        return self.viewIterator(result)

    def queryConcepts(self):
        result = set()
        cat = self.catalog
        request = self.request
        type = request.get('search.3.type', 'loops:concept:*')
        text = request.get('search.3.text')
        if not text and '*' in type:
            return None
        if type.endswith('*'):
            start = type[:-1]
            end = start + '\x7f'
        else:
            start = end = type
        criteria = {'loops_type': (start, end),}
        if text:
            criteria['loops_title'] = text
        queue = list(cat.searchResults(**criteria))
        concepts = []
        while queue:
            c = queue.pop(0)
            concepts.append(c)
            for child in c.getChildren():
                # TODO: check for tree level, use relevance factors, ...
                if child not in queue and child not in concepts:
                    queue.append(child)
        for c in concepts:
            result.add(c)
            result.update(c.getResources())
        return result

