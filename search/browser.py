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

from zope import interface, component
from zope.app.catalog.interfaces import ICatalog
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.namedtemplate import NamedTemplate, NamedTemplateImplementation
from zope.i18nmessageid import MessageFactory

from cybertools.ajax import innerHtml
from loops.browser.common import BaseView

_ = MessageFactory('zope')

template = ViewPageTemplateFile('search.pt')

class Search(BaseView):

    maxRowNum = 0

    template = template

    @Lazy
    def macro(self):
        return template.macros['search']

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
    def results(self):
        request = self.request
        type = request.get('search.1.text', 'loops:resource:*')
        text = request.get('search.2.text')
        if not text and '*' in type: # there should be some sort of selection...
            return set()
        useTitle = request.get('search.2.title')
        useFull = request.get('search.2.full')
        r1 = set()
        cat = component.getUtility(ICatalog)
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
        result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        result.sort(key=lambda x: x.title.lower())
        return self.viewIterator(result)

