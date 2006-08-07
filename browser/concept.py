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
Definition of the concept view classes.

$Id$
"""

from zope import interface, component, schema
from zope.app import zapi
from zope.app.catalog.interfaces import ICatalog
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.container.contained import ObjectRemovedEvent
from zope.app.form.browser.interfaces import ITerms
from zope.app.form.interfaces import IDisplayWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.formlib.form import EditForm, FormFields
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import implements
from zope.publisher.interfaces import BadRequest
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.schema.interfaces import IIterableSource
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import IType, ITypeManager
from loops.interfaces import IConcept
from loops.concept import Concept, ConceptTypeSourceList, PredicateSourceList
from loops.browser.common import EditForm, BaseView, LoopsTerms
from loops import util


class ConceptEditForm(EditForm):

    @Lazy
    def typeInterface(self):
        return IType(self.context).typeInterface

    @property
    def form_fields(self):
        fields = FormFields(IConcept)
        typeInterface = self.typeInterface
        if typeInterface is not None:
            fields = FormFields(fields, typeInterface)
        return fields


class ConceptView(BaseView):

    template = NamedTemplate('loops.concept_macros')

    @Lazy
    def macro(self):
        return self.template.macros['conceptdata']

    def fieldData(self):
        ti = IType(self.context).typeInterface
        if not ti: return
        adapter = ti(self.context)
        for n, f in schema.getFieldsInOrder(ti):
            value = getattr(adapter, n, '')
            if not value:
                continue
            bound = f.bind(adapter)
            widget = component.getMultiAdapter(
                                (bound, self.request), IDisplayWidget)
            widget.setRenderedValue(value)
            yield dict(title=f.title, value=value, id=n, widget=widget)

    def children(self):
        cm = self.loopsRoot.getConceptManager()
        hasType = cm.getTypePredicate()
        standard = cm.getDefaultPredicate()
        for r in self.context.getChildRelations():
            if r.predicate == hasType:
                # only show top-level entries for type instances:
                skip = False
                for parent in r.second.getParents((standard,)):
                    if parent.conceptType == self.context:
                        skip = True
                        break
                if skip: continue
            yield ConceptRelationView(r, self.request, contextIsSecond=True)

    def parents(self):
        for r in self.context.getParentRelations():
            yield ConceptRelationView(r, self.request)

    def resources(self):
        for r in self.context.getResourceRelations():
            yield ConceptRelationView(r, self.request, contextIsSecond=True)

    @Lazy
    def view(self):
        viewName = self.request.get('loops.viewName') or getattr(self, '_viewName', None)
        if not viewName:
            ti = IType(self.context).typeInterface
            # TODO: check the interface (maybe for a base interface IViewProvider)
            #       instead of the viewName attribute:
            if ti and 'viewName' in ti:
                typeAdapter = ti(self.context)
                viewName = typeAdapter.viewName
        if viewName:
            # ??? Would it make sense to use a somehow restricted interface
            #     that should be provided by the view like IQuery?
            #viewInterface = getattr(typeAdapter, 'viewInterface', None) or IQuery
            adapter = component.queryMultiAdapter((self.context, self.request),
                                        interface.Interface, name=viewName)
            if adapter is not None:
                return adapter
        #elif type provides view: use this
        return self


class ConceptConfigureView(ConceptView):

    def update(self):
        request = self.request
        action = request.get('action')
        if action is None:
            return True
        if action == 'create':
            self.createAndAssign()
            return True
        tokens = request.get('tokens', [])
        for token in tokens:
            parts = token.split(':')
            token = parts[0]
            if len(parts) > 1:
                relToken = parts[1]
            concept = self.loopsRoot.loopsTraverse(token)
            if action == 'assign':
                assignAs = request.get('assignAs', 'child')
                predicate = request.get('predicate') or None
                if predicate:
                    predicate = removeSecurityProxy(
                                    self.loopsRoot.loopsTraverse(predicate))
                if assignAs == 'child':
                    self.context.assignChild(removeSecurityProxy(concept), predicate)
                elif assignAs == 'parent':
                    self.context.assignParent(removeSecurityProxy(concept), predicate)
                elif assignAs == 'resource':
                    self.context.assignResource(removeSecurityProxy(concept), predicate)
                else:
                    raise(BadRequest, 'Illegal assignAs parameter: %s.' % assignAs)
            elif action == 'remove':
                predicate = self.loopsRoot.loopsTraverse(relToken)
                qualifier = request.get('qualifier')
                if qualifier == 'parents':
                    self.context.deassignParent(concept, [predicate])
                elif qualifier == 'children':
                    self.context.deassignChild(concept, [predicate])
                elif qualifier == 'resources':
                    self.context.deassignResource(concept, [predicate])
                elif qualifier == 'concepts':
                    self.context.deassignConcept(concept, [predicate])
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
        token = self.request.get('create.type')
        type = ITypeManager(self.context).getType(token)
        factory = type.factory
        container = type.defaultContainer
        concept = removeSecurityProxy(factory(title))
        container[name] = concept
        if IConcept.providedBy(concept):
            concept.conceptType = type.typeProvider
        notify(ObjectCreatedEvent(concept))
        notify(ObjectModifiedEvent(concept))
        assignAs = self.request.get('assignAs', 'child')
        predicate = request.get('create.predicate') or None
        if predicate:
            predicate = removeSecurityProxy(
                            self.loopsRoot.loopsTraverse(predicate))
        if assignAs == 'child':
            self.context.assignChild(concept, predicate)
        elif assignAs == 'parent':
            self.context.assignParent(concept, predicate)
        elif assignAs == 'resource':
            self.context.assignResource(concept, predicate)
        elif assignAs == 'concept':
            self.context.assignConcept(concept, predicate)
        else:
            raise(BadRequest, 'Illegal assignAs parameter: %s.' % assignAs)

    def search(self):
        request = self.request
        if request.get('action') != 'search':
            return []
        searchTerm = request.get('searchTerm', None)
        searchType = request.get('searchType', None)
        result = []
        if searchTerm or searchType != 'none':
            criteria = {}
            if searchTerm:
                criteria['loops_title'] = searchTerm
            if searchType:
                if searchType.endswith('*'):
                    start = searchType[:-1]
                    end = start + '\x7f'
                else:
                    start = end = searchType
                criteria['loops_type'] = (start, end)
            cat = zapi.getUtility(ICatalog)
            result = cat.searchResults(**criteria)
            # TODO: can this be done in a faster way?
            result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        else:
            result = self.loopsRoot.getConceptManager().values()
        if searchType == 'none':
            result = [r for r in result if r.conceptType is None]
        return self.viewIterator(result)

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
                yield BaseView(o, request)

    def conceptTypes(self):
        return util.KeywordVocabulary([(t.token, t.title)
                    for t in ITypeManager(self.context).listTypes(('concept',))])

    def conceptTypesForSearch(self):
        general = [('loops:concept:*', 'Any'),]
        return util.KeywordVocabulary(general + [(t.tokenForSearch, t.title)
                    for t in ITypeManager(self.context).listTypes(('concept',))])

    def resourceTypes(self):
        return util.KeywordVocabulary([(t.token, t.title)
                    for t in ITypeManager(self.context).listTypes(('resource',))])

    def resourceTypesForSearch(self):
        general = [('loops:resource:*', 'Any'),]
        return util.KeywordVocabulary(general + [(t.tokenForSearch, t.title)
                    for t in ITypeManager(self.context).listTypes(('resource',))])

    def predicates(self):
        preds = PredicateSourceList(self.context)
        terms = zapi.getMultiAdapter((preds, self.request), ITerms)
        for pred in preds:
            yield terms.getTerm(pred)


class ConceptRelationView(BaseView):

    def __init__(self, relation, request, contextIsSecond=False):
        if contextIsSecond:
            self.context = relation.second
            self.other = relation.first
        else:
            self.context = relation.first
            self.other = relation.second
        self.predicate = relation.predicate
        self.request = request

    @Lazy
    def token(self):
        return ':'.join((self.loopsRoot.getLoopsUri(self.context),
                         self.loopsRoot.getLoopsUri(self.predicate)))

    @Lazy
    def isProtected(self):
        return zapi.getName(self.predicate) == 'hasType'

    @Lazy
    def predicateTitle(self):
        return self.predicate.title

    @Lazy
    def predicateUrl(self):
        return zapi.absoluteURL(self.predicate, self.request)

