#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
loops.expert package.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getParent

from cybertools.browser.form import FormController
from cybertools.stateful.interfaces import IStateful, IStatesDefinition
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted, AdapterBase
from loops.expert.concept import ConceptQuery, FullQuery
from loops.interfaces import IResource
from loops.organize.personal.browser.filter import FilterView
from loops.security.common import canWriteObject, checkPermission
from loops import util
from loops.util import _


search_template = ViewPageTemplateFile('search.pt')


class QuickSearchResults(NodeView):
    """ Provides results listing """

    showActions = False

    @Lazy
    def search_macros(self):
        return self.controller.getTemplateMacros('search', search_template)

    @Lazy
    def macro(self):
        return self.search_macros['quicksearch_view']

    @Lazy
    def item(self):
        return self

    @Lazy
    def results(self):
        form = self.request.form
        text = form.get('search.text')
        type = self.globalOptions('expert.quicksearch')
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=True, useFull=True,)
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result.sort(key=lambda x: x.title.lower())
        return self.viewIterator(result)


class Search(ConceptView):

    form_action = 'execute_search_action'
    maxRowNum = 0

    @Lazy
    def search_macros(self):
        return self.controller.getTemplateMacros('search', search_template)

    @Lazy
    def macro(self):
        return self.search_macros['search']

    @Lazy
    def showActions(self):
        return checkPermission('loops.ManageSite', self.context)
        #return canWriteObject(self.context)

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
        result = ConceptQuery(self).query(type=token)
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result.sort(key=lambda x: x.title)
        noSelection = dict(token='none', title=u'not selected')
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

    def listConcepts(self, filterMethod=None):
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
                                                 exclude=('hidden',))
                fv = FilterView(self.context, self.request)
                result = fv.apply(result)
                for o in result:
                    if o.getLoopsRoot() == self.loopsRoot:
                        adObj = adapted(o, self.languageInfo)
                        if filterMethod is not None and not filterMethod(adObj):
                            continue
                        name = self.getRowName(adObj) or u''
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
        for item in data[:100]:
            json.append("{label: '%s', name: '%s', id: '%s'}" %
                          (item['label'], item['name'], item['id']))
        json = "{identifier: 'id', items: [%s]}" % ', '.join(json)
        #print '***', json
        return json

    def executeQuery(self, **kw):
        return ConceptQuery(self).query(**kw)

    def getRowName(self, obj):
        return obj.getLongTitle()

    def getRowLabel(self, obj, name=None):
        if isinstance(obj, AdapterBase):
            obj = obj.context
        if name is None:
            name = obj.title
        return '%s (%s)' % (name, obj.conceptType.title)

    @Lazy
    def statesDefinitions(self):
        stdnames = (self.globalOptions('organize.stateful.resource', []) +
                    self.globalOptions('organize.stateful.special', []))
        return [component.getUtility(IStatesDefinition, name=n) for n in stdnames]

    @Lazy
    def selectedStates(self):
        result = {}
        for k, v in self.request.form.items():
            if k.startswith('state.') and v:
                result[k] = v
        return result

    def submitReplacing(self, targetId, formId, view):
        self.registerDojo()
        return 'submitReplacing("%s", "%s", "%s"); return false;' % (
                    targetId, formId,
                    '%s/.target%s/@@searchresults.html' % (view.url, self.uniqueId))

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
        result = [r for r in result if self.checkStates(r)]
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result = sorted(result, key=lambda x: x.title and x.title.lower())
        return self.viewIterator(result)

    def checkStates(self, obj):
        if not IResource.providedBy(obj):
            return True
        for std, states in self.selectedStates.items():
            if std.startswith('state.resource.'):
                std = std[len('state.resource.'):]
            elif std.startswith('state.'):
                std = std[len('state.'):]
            else:
                continue
            stf = component.queryAdapter(obj, IStateful, name=std)
            if stf is None:
                continue
            for state in states:
                if stf.state == state:
                    break
                else:
                    return False
        return True


class SearchResults(NodeView):
    """ Provides results as inner HTML - not used any more (?)"""

    @Lazy
    def search_macros(self):
        return self.controller.getTemplateMacros('search', search_template)

    @Lazy
    def macro(self):
        return self.search_macros['search_results']

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
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result = sorted(result, key=lambda x: x.title.lower())
        return self.viewIterator(result)


class ActionExecutor(FormController):

    def update(self):
        form = self.request.form
        actions = [k for k in form.keys() if k.startswith('action.')]
        if actions:
            action = actions[0].split('.', 1)[1]
            uids = form.get('selection', [])
            if uids:
                method = self.actions.get(action)
                if method:
                    method(self, uids)
        return True

    def delete(self, uids):
        self.request.form['message'] = _(
                u'The objects selected have been deleted.')
        for uid in uids:
            obj = util.getObjectForUid(uid)
            if not canWriteObject(obj):
                continue
            parent = getParent(obj)
            del parent[getName(obj)]

    def change_state(self, uids):
        stdefs = dict([(k.split('.', 1)[1], v)
                        for k, v in self.request.form.items()
                        if k.startswith('trans.') and self.request.form[k] != '-'])
        if not stdefs:
            return
        for uid in uids:
            obj = util.getObjectForUid(uid)
            if not canWriteObject(obj):
                continue
            for stdef, trans in stdefs.items():
                stf = component.getAdapter(obj, IStateful, name=stdef)
                if trans in [t.name for t in stf.getAvailableTransitions()]:
                    stf.doTransition(trans)
        self.request.form['message'] = _(
                u'The state of the objects selected has been changed.')

    actions = dict(delete=delete, change_state=change_state)
