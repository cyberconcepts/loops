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
from zope import traversing
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.namedtemplate import NamedTemplate, NamedTemplateImplementation
from zope.i18nmessageid import MessageFactory

from cybertools.ajax import innerHtml
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.typology.interfaces import ITypeManager
from loops.browser.common import BaseView
from loops.query import ConceptQuery, FullQuery
from loops import util
from loops.util import _


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
        title = request.get('searchString', '').replace('(', ' ').replace(')', ' ')
        type = request.get('searchType') or 'loops:concept:*'
        result = ConceptQuery(self).query(title=title, type=type)
        registry = component.getUtility(IRelationRegistry)
        # simple way to provide JSON format:
        return str(sorted([[`o.title`[2:-1] + ' (%s)' % `o.conceptType.title`[2:-1],
                            `registry.getUniqueIdForObject(o)`]
                        for o in result
                        if o.getLoopsRoot() == self.loopsRoot])).replace('\\\\x', '\\x')
        #return str(sorted([[`o.title`[2:-1], `traversing.api.getName(o)`[2:-1]]
        #                for o in result])).replace('\\\\x', '\\x')

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
        type = request.get('search.1.text', 'loops:*')
        text = request.get('search.2.text')
        useTitle = request.get('search.2.title')
        useFull = request.get('search.2.full')
        conceptType = request.get('search.3.type', 'loops:concept:*')
        conceptTitle = request.get('search.3.text')
        conceptUid = request.get('search.3.text_selected')
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=useTitle, useFull=useFull,
                           conceptTitle=conceptTitle, conceptUid=conceptUid,
                           conceptType= conceptType)
        result = sorted(result, key=lambda x: x.title.lower())
        return self.viewIterator(result)

