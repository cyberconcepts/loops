#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
from loops.browser.node import NodeView
from loops.common import adapted, AdapterBase
from loops.expert.concept import ConceptQuery, FullQuery
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
        jsCall = ('dojo.require("dojo.parser");'
                  'dojo.require("dijit.form.FilteringSelect");'
                  'dojo.require("dojox.data.QueryReadStore");')
        cm.register('js-execute', jsCall, jsCall=jsCall)

    def listConcepts(self):
        """ Used for dijit.FilteringSelect.
        """
        request = self.request
        request.response.setHeader('Content-Type', 'text/plain; charset=UTF-8')
        title = request.get('name')
        if title == '*':
            title = None
        types = request.get('searchType')
        data = []
        if title or types:
            if title is not None:
                title = title.replace('(', ' ').replace(')', ' ').replace(' -', ' ')
                #title = title.split(' ', 1)[0]
            if not types:
                types = ['loops:concept:*']
            if not isinstance(types, (list, tuple)):
                types = [types]
            for type in types:
                result = self.executeQuery(title=title or None, type=type,
                                                 exclude=('system',))
                for o in result:
                    if o.getLoopsRoot() == self.loopsRoot:
                        adObj = adapted(o, self.languageInfo)
                        name = self.getRowName(adObj)
                        if title and title.endswith('*'):
                            title = title[:-1]
                        sort = ((title and name.startswith(title) and '0' or '1')
                                + name.lower())
                        if o.conceptType is None:
                            raise ValueError('Concept Type missing for %r.' % name)
                        data.append({'label': self.getRowLabel(adObj, name),
                                     'name': name,
                                     'id': util.getUidForObject(o),
                                     'sort': sort})
        data.sort(key=lambda x: x['sort'])
        if not title:
            data.insert(0, {'label': '', 'name': '', 'id': ''})
        json = []
        for item in data[:20]:
            json.append("{label: '%s', name: '%s', id: '%s'}" %
                          (item['label'], item['name'], item['id']))
        json = "{identifier: 'id', items: [%s]}" % ', '.join(json)
        #print '***', json
        return json

    def executeQuery(self, **kw):
        return ConceptQuery(self).query(**kw)

    def getRowName(self, obj):
        return obj.title

    def getRowLabel(self, obj, name):
        if isinstance(obj, AdapterBase):
            obj = obj.context
        return '%s (%s)' % (name, obj.conceptType.title)

    def submitReplacing(self, targetId, formId, view):
        self.registerDojo()
        return 'submitReplacing("%s", "%s", "%s"); return false;' % (
                    targetId, formId,
                    '%s/.target%s/@@searchresults.html' % (view.url, self.uniqueId))


#class SearchResults(BaseView):
class SearchResults(NodeView):
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
        #conceptTitle = form.get('search.3.text')
        #if conceptTitle is not None:
        #    conceptTitle = util.toUnicode(conceptTitle, encoding='ISO8859-15')
        conceptUid = form.get('search.3.text')
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=useTitle, useFull=useFull,
                           #conceptTitle=conceptTitle,
                           conceptUid=conceptUid,
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

