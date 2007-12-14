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
from loops.common import adapted
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

    @Lazy
    def presetSearchTypes(self):
        """ Return a list of concept type info dictionaries (see BaseView)
            that should be displayed on a separate search parameter row.
        """
        #return ITypeManager(self.context).listTypes(include=('search',))
        return self.listTypesForSearch(include=('search',))

    def conceptsForType(self, token):
        noSelection = dict(token='none', title=u'not selected')
        result = sorted(ConceptQuery(self).query(type=token), key=lambda x: x.title)
        return [noSelection] + [dict(title=adapted(o, self.languageInfo).title,
                                     token=util.getUidForObject(o))
                                    for o in result]

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
        result = ConceptQuery(self).query(title=title, type=type, exclude=('system',))
        #registry = component.getUtility(IRelationRegistry)
        # simple way to provide JSON format:
        return str(sorted([[`adapted(o, self.languageInfo).title`[2:-1]
                                + ' (%s)' % `o.conceptType.title`[2:-1],
                            `int(util.getUidForObject(o))`]
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
        form = self.request.form
        type = form.get('search.1.text', 'loops:*')
        text = form.get('search.2.text')
        if text is not None:
            text = util.toUnicode(text, encoding='ISO8859-15') # IE hack!!!
        useTitle = form.get('search.2.title')
        useFull = form.get('search.2.full')
        conceptType = form.get('search.3.type', 'loops:concept:*')
        conceptTitle = form.get('search.3.text')
        if conceptTitle is not None:
            conceptTitle = util.toUnicode(conceptTitle, encoding='ISO8859-15')
        conceptUid = form.get('search.3.text_selected')
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=useTitle, useFull=useFull,
                           conceptTitle=conceptTitle, conceptUid=conceptUid,
                           conceptType=conceptType)
        rowNum = 4
        while rowNum < 10:
            addCriteria = form.get('search.%i.text_selected' % rowNum)
            rowNum += 1
            if not addCriteria:
                break
            if addCriteria == 'none':
                continue
            addSelection = FullQuery(self).query(text=text, type=type,
                                useTitle=useTitle, useFull=useFull,
                                conceptUid=addCriteria)
            if result:
                result = [r for r in result if r in addSelection]
            else:
                result = addSelection
        result = sorted(result, key=lambda x: x.title.lower())
        return self.viewIterator(result)

