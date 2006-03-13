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
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.app.form.browser.interfaces import ITerms
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.formlib.form import EditForm, FormFields
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import implements
from zope.publisher.interfaces import BadRequest
from zope.publisher.interfaces.browser import IBrowserRequest
from zope import schema
from zope.schema.interfaces import IIterableSource
from zope.security.proxy import removeSecurityProxy
from loops.interfaces import IConcept
from loops.concept import Concept, ConceptTypeSourceList, PredicateSourceList
from loops.resource import getResourceTypes, getResourceTypesForSearch
from loops.target import getTargetTypes
from loops.browser.common import BaseView, LoopsTerms
from loops import util


class ConceptEditForm(EditForm):

    form_fields = FormFields(IConcept)
    template = NamedTemplate('pageform')


class ConceptView(BaseView):

    def children(self):
        for r in self.context.getChildRelations():
            yield ConceptRelationView(r, self.request, contextIsSecond=True)

    def parents(self):
        for r in self.context.getParentRelations():
            yield ConceptRelationView(r, self.request)

    def resources(self):
        for r in self.context.getResourceRelations():
            yield ConceptResourceRelationView(r, self.request, contextIsSecond=True)


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
        conceptType = request.get('create.type')
        if conceptType and conceptType.startswith('loops.resource.'):
            factory = resolve(conceptType)
            concept = factory(title)
            container = self.loopsRoot.getResourceManager()
        else:
            concept = Concept(title)
            container = self.loopsRoot.getConceptManager()
        container[name] = concept
        if conceptType:
            ctype = self.loopsRoot.loopsTraverse(conceptType)
            concept.conceptType = ctype
        notify(ObjectCreatedEvent(removeSecurityProxy(concept)))
        assignAs = self.request.get('assignAs', 'child')
        predicate = request.get('create.predicate') or None
        if predicate:
            predicate = removeSecurityProxy(
                            self.loopsRoot.loopsTraverse(predicate))
        if assignAs == 'child':
            self.context.assignChild(removeSecurityProxy(concept), predicate)
        elif assignAs == 'parent':
            self.context.assignParent(removeSecurityProxy(concept), predicate)
        elif assignAs == 'resource':
            self.context.assignResource(removeSecurityProxy(concept), predicate)
        elif assignAs == 'concept':
            self.context.assignConcept(removeSecurityProxy(concept), predicate)
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
        else:
            result = self.loopsRoot.getConceptManager().values()
        if searchType == 'none':
            result = [r for r in result if r.conceptType is None]
        return self.viewIterator(result)

    @Lazy
    def typeTitle(self):
        return self.context.conceptType.title

    @Lazy
    def typeUrl(self):
        return zapi.absoluteURL(self.context.conceptType, self.request)

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            if IConcept.providedBy(o):
                yield ConceptConfigureView(o, request)
            else:
                yield BaseView(o, request)

    def conceptTypes(self):
        types = ConceptTypeSourceList(self.context)
        terms = zapi.getMultiAdapter((types, self.request), ITerms)
        for type in types:
            yield terms.getTerm(type)

    def conceptTypesForSearch(self):
        types = ConceptTypeSourceList(self.context)
        typesItems = [(':'.join(('loops:concept',
                                 self.getConceptTypeTokenForSearch(t))), t.title)
                       for t in types]
        return util.KeywordVocabulary(typesItems)

    def getConceptTypeTokenForSearch(self, ct):
        return ct is None and 'unknown' or zapi.getName(ct)

    def resourceTypes(self):
        return util.KeywordVocabulary(getResourceTypes())

    def resourceTypesForSearch(self):
        return util.KeywordVocabulary(getResourceTypesForSearch())


    def predicates(self):
        preds = PredicateSourceList(self.context)
        terms = zapi.getMultiAdapter((preds, self.request), ITerms)
        for pred in preds:
            yield terms.getTerm(pred)


class ConceptRelationView(object):

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
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def url(self):
        return zapi.absoluteURL(self.context, self.request)

    @Lazy
    def title(self):
        return self.context.title
    
    @Lazy
    def token(self):
        return ':'.join((self.loopsRoot.getLoopsUri(self.context),
                         self.loopsRoot.getLoopsUri(self.predicate)))

    @Lazy
    def conceptType(self):
        return self.context.conceptType

    @Lazy
    def typeTitle(self):
        return self.conceptType.title

    @Lazy
    def typeUrl(self):
        return zapi.absoluteURL(self.conceptType, self.request)

    @Lazy
    def predicateTitle(self):
        return self.predicate.title

    @Lazy
    def predicateUrl(self):
        return zapi.absoluteURL(self.predicate, self.request)


class ConceptResourceRelationView(ConceptRelationView):
    
    @Lazy
    def conceptType(self):
        return None

    @Lazy
    def typeTitle(self):
        voc = util.KeywordVocabulary(getTargetTypes())
        token = '.'.join((self.context.__module__,
                          self.context.__class__.__name__))
        term = voc.getTermByToken(token)
        return term.title


    @Lazy
    def typeUrl(self):
        return ''

