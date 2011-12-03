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
Definition of the concept view classes.
"""

from itertools import groupby
from zope import interface, component, schema
from zope.app.catalog.interfaces import ICatalog
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.container.contained import ObjectRemovedEvent
from zope.app.form.browser.interfaces import ITerms
from zope.app.form.interfaces import IDisplayWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.formlib.form import EditForm, FormFields, setUpEditWidgets
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import implements
from zope.publisher.interfaces import BadRequest
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.schema.interfaces import IIterableSource
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName
from zope.traversing.browser import absoluteURL

from cybertools.browser.action import actions
from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.grid.interfaces import Grid
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.meta.interfaces import IOptions
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.util.jeep import Jeep
from loops.browser.common import EditForm, BaseView, LoopsTerms, concept_macros
from loops.common import adapted
from loops.concept import Concept, ConceptTypeSourceList, PredicateSourceList
from loops.i18n.browser import I18NView
from loops.interfaces import IConcept, IConceptSchema, ITypeConcept, IResource
from loops.organize.util import getRolesForPrincipal
from loops.schema.base import RelationSet, Relation
from loops import util
from loops.util import _
from loops.versioning.util import getVersion


class ConceptEditForm(EditForm, I18NView):
    """ Classic-style (zope.formlib-based) form for editing concepts.
    """

    ignoredFieldTypes = (Grid, Relation, RelationSet,)

    #@Lazy  # zope.formlib does not issue a redirect after changes, so that
            # it tries to redisplay the old form even after a type change that
            # changes the set of available attributes. So the typeInterface
            # must be recalculated e.g. after an update of the context object.
    @property
    def typeInterface(self):
        return IType(self.context).typeInterface

    @Lazy
    def title(self):
        return adapted(self.context, self.languageInfo).title

    @property
    def form_fields(self):
        typeInterface = self.typeInterface
        if typeInterface is None:
            fields = FormFields(IConcept)
        elif 'title' in typeInterface:  # new type interface based on ConceptSchema
            f1 = FormFields(IConcept).omit('title', 'description')
            fields = FormFields(typeInterface, f1)
        else:
            fields = FormFields(IConcept, typeInterface)
        return [f for f in fields
                  if not isinstance(f.field, self.ignoredFieldTypes)]

    def setUpWidgets(self, ignore_request=False):
        # TODO: get rid of removeSecurityProxy(): use ConceptSchema in interfaces
        #adapter = removeSecurityProxy(adapted(self.context, self.languageInfo))
        adapter = adapted(self.context, self.languageInfo)
        self.adapters = {self.typeInterface: adapter,
                         IConceptSchema: adapter}
        self.widgets = setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request)
        desc = self.widgets.get('description')
        if desc:
            desc.height = 2


class BaseRelationView(BaseView):
    """ For displaying children and resources lists.
    """

    def __init__(self, relation, request, contextIsSecond=False):
        if contextIsSecond:
            self.context = relation.second
            self.other = relation.first
        else:
            self.context = relation.first
            self.other = relation.second
        self.context = getVersion(self.context, request)
        self.predicate = relation.predicate
        self.predicates = [self.predicate]  # allow for more than one relation
        self.relation = relation
        self.relations = [relation]
        self.request = request

    @Lazy
    def hash(self):
        return '%s:%s' % (id(self.relation.first), id(self.relation.second))

    @Lazy
    def adapted(self):
        return adapted(self.context, self.languageInfo)

    @Lazy
    def data(self):
        return self.getData()

    def getData(self):
        return self.instance.applyTemplate()

    @Lazy
    def instance(self):
        instance = IInstance(self.adapted)
        instance.template = self.schema
        instance.view = self
        return instance

    @Lazy
    def schema(self):
        ti = self.typeInterface or IConceptSchema
        schemaFactory = component.getAdapter(self.adapted, ISchemaFactory)
        return schemaFactory(ti, manager=self, request=self.request)

    @Lazy
    def title(self):
        return self.adapted.title or getName(self.context)

    @Lazy
    def description(self):
        return self.adapted.description

    @Lazy
    def token(self):
        return ':'.join((self.loopsRoot.getLoopsUri(self.context),
                         self.loopsRoot.getLoopsUri(self.predicate)))

    @Lazy
    def uidToken(self):
        return ':'.join((util.getUidForObject(self.context),
                         util.getUidForObject(self.predicate)))

    @Lazy
    def isProtected(self):
        return getName(self.predicate) == 'hasType'

    @Lazy
    def predicateTitle(self):
        return ', ' .join(p.title for p in self.predicates)

    @Lazy
    def predicateUrl(self):
        return absoluteURL(self.predicate, self.request)

    @Lazy
    def relevance(self):
        return self.relation.relevance

    @Lazy
    def order(self):
        return self.relation.order

    @Lazy
    def relationInfo(self):
        if self.predicate == self.defaultPredicate:
            return u''
        return self.predicateTitle


class ConceptView(BaseView):

    template = concept_macros

    def childViewFactory(self, *args, **kw):
        return ConceptRelationView(*args, **kw)

    @Lazy
    def macro(self):
        return self.template.macros['conceptdata']

    #def __init__(self, context, request):
    #    super(ConceptView, self).__init__(context, request)

    def setupController(self):
        cont = self.controller
        if cont is None:
            return
        if self.parentsForPortlet and (
                self.globalOptions('showParentsForAnonymous') or
                not IUnauthenticatedPrincipal.providedBy(self.request.principal)):
            cont.macros.register('portlet_right', 'parents', title=_(u'Parents'),
                        subMacro=concept_macros.macros['parents'],
                        priority=20, info=self)

    @Lazy
    def adapted(self):
        return adapted(self.context, self.languageInfo)

    @Lazy
    def title(self):
        return self.adapted.title or getName(self.context)

    @Lazy
    def description(self):
        return self.adapted.description

    def breadcrumbs(self):
        data = []
        if self.breadcrumbsParent is not None:
            data.extend(self.breadcrumbsParent.breadcrumbs())
        if self.context != self.nodeView.targetObject:
            data.append(dict(label=self.title,
                             url=self.nodeView.getUrlForTarget(self.context)))
        return data

    @Lazy
    def breadcrumbsParent(self):
        return None

    def getData(self, omit=('title', 'description')):
        data = self.instance.applyTemplate()
        for k in omit:
            if k in data:
                del data[k]
        return data

    @Lazy
    def data(self):
        return self.getData()

    def getFields(self, omit=('title', 'description')):
        fields = Jeep(self.schema.fields)
        fields.remove(*omit)
        return fields

    @Lazy
    def fields(self):
        return self.getFields()

    @Lazy
    def schema(self):
        ti = self.typeInterface or IConceptSchema
        schemaFactory = component.getAdapter(self.adapted, ISchemaFactory)
        return schemaFactory(ti, manager=self, request=self.request)

    @Lazy
    def instance(self):
        instance = IInstance(self.adapted)
        instance.template = self.schema
        instance.view = self
        return instance

    def reorderChildren(self, tokens):
        for r in self.context.getChildRelations(sort=None):
            token = ':'.join((util.getUidForObject(r.second),
                              util.getUidForObject(r.predicate)))
            if token in tokens:
                pos = tokens.index(token) + 1
                if r.order != pos:
                    r.order = pos

    def getChildren(self, topLevelOnly=True, sort=True, noDuplicates=True,
                    useFilter=True):
        form = self.request.form
        #if form.get('loops.viewName') == 'index.html' and self.editable:
        if self.editable:
            self.registerDojoDnd()
            if 'children_change_order' in form:
                tokens = form.get('child_tokens')
                if tokens:
                    self.reorderChildren(tokens)
        cm = self.loopsRoot.getConceptManager()
        hasType = cm.getTypePredicate()
        params = self.params
        criteria = {}
        if params.get('types'):
            criteria['types'] = [cm.get(name) for name in params['types']]
        standard = cm.getDefaultPredicate()
        rels = (self.childViewFactory(r, self.request, contextIsSecond=True)
                for r in self.context.getChildRelations(sort=None))
        if sort:
            rels = sorted(rels, key=lambda r: (r.order, r.title.lower()))
        from loops.organize.personal.browser.filter import FilterView
        fv = FilterView(self.context, self.request)
        for r in rels:
            if criteria:
                if not self.checkCriteria(r, criteria):
                    continue
            if topLevelOnly and r.predicate == hasType:
                # only show top-level entries for type instances:
                skip = False
                for parent in r.context.getParents((standard,)):
                    if parent.conceptType == self.context:
                        skip = True
                        break
                if skip:
                    continue
            if useFilter:
                options = IOptions(adapted(r.predicate), None)
                if options is not None and options('hide_children'):
                    continue
                if not fv.check(r.context):
                    continue
            yield r

    def checkCriteria(self, relation, criteria):
        result = True
        for k, v in criteria.items():
            if k == 'types':
                v = [item for item in v if item is not None]
                result = result and (relation.context.conceptType in v)
        return result

    # Override in subclass to control what is displayd in listings:
    children = getChildren

    def childrenAlphaGroups(self):
        result = Jeep()
        rels = self.getChildren(topLevelOnly=False, sort=False)
        rels = sorted(rels, key=lambda r: r.title.lower())
        for letter, group in groupby(rels, lambda r: r.title.lower()[0]):
            letter = letter.upper()
            result[letter] = list(group)
        return result

    def childrenByType(self):
        result = Jeep()
        rels = self.getChildren(topLevelOnly=False, sort=False)
        rels = sorted(rels, key=lambda r: (r.typeTitle.lower(), r.title.lower()))
        for type, group in groupby(rels, lambda r: r.type):
            typeName = getName(type.typeProvider)
            result[typeName] = list(group)
        return result

    def isHidden(self, pr):
        predOptions = IOptions(adapted(pr.predicate))
        if predOptions('hide_parents'):
            return True
        if (getName(pr.second.conceptType) in predOptions('hide_parents_for', [])):
            return True
        hideRoles = None
        options = component.queryAdapter(adapted(pr.first), IOptions)
        if options is not None:
            hideRoles = options('hide_for', None)
        if not hideRoles:
            hideRoles = IOptions(adapted(pr.first.conceptType))('hide_for', None)
        if hideRoles is not None:
            principal = self.request.principal
            if (IUnauthenticatedPrincipal.providedBy(principal) and
                'zope.Anonymous' in hideRoles):
                return True
            roles = getRolesForPrincipal(principal.id, self.context)
            for r in roles:
                if r in hideRoles:
                    return True
        return False

    @Lazy
    def parentsForPortlet(self):
        return [p for p in self.parents() if not self.isHidden(p.relation)]

    def parents(self):
        rels = sorted(self.context.getParentRelations(),
                      key=(lambda x: x.first.title and x.first.title.lower()))
        for r in rels:
            yield self.childViewFactory(r, self.request)

    def reorderResources(self, tokens):
        for r in self.context.getResourceRelations(sort=None):
            token = ':'.join((util.getUidForObject(r.second),
                              util.getUidForObject(r.predicate)))
            if token in tokens:
                pos = tokens.index(token) + 1
                if r.order != pos:
                    r.order = pos

    def resources(self):
        form = self.request.form
        #if form.get('loops.viewName') == 'index.html' and self.editable:
        if self.editable:
            self.registerDojoDnd()
            if 'resources_change_order' in form:
                tokens = form.get('resources_tokens')
                if tokens:
                    self.reorderResources(tokens)
        from loops.browser.resource import ResourceRelationView
        from loops.organize.personal.browser.filter import FilterView
        fv = FilterView(self.context, self.request)
        rels = self.context.getResourceRelations()
        for r in rels:
            if fv.check(r.first):
                yield ResourceRelationView(r, self.request, contextIsSecond=True)

    @Lazy
    def resourcesList(self):
        from loops.browser.resource import ResourceRelationView
        return [ResourceRelationView(r, self.request, contextIsSecond=True)
                    for r in self.context.getResourceRelations()]

    @Lazy
    def resourcesByType(self):
        result = dict(texts=[], images=[], files=[])
        for rv in self.resourcesList:
            r = rv.context
            if r.contentType.startswith('text/'):
                result['texts'].append(r)
            if r.contentType.startswith('image/'):
                result['images'].append(r)
            else:
                result['files'].append(r)
        return result

    def unique(self, rels):
        result = Jeep()
        for r in rels:
            existing = result.get(r.hash)
            if existing is not None:
                existing.relations.append(r)
                existing.predicates.append(r.predicate)
            else:
                result[r.hash] = r
        return result.values()

    @Lazy
    def view(self):
        context = self.context
        name = self.request.get('loops.viewName') or getattr(self, '_viewName', None)
        if not name:
            ti = IType(context).typeInterface
            # TODO: check the interface (maybe for a base interface IViewProvider)
            #       instead of the viewName attribute:
            if ti and ti != ITypeConcept and 'viewName' in ti:
                typeAdapter = ti(self.context)
                name = typeAdapter.viewName
        if not name:
            tp = IType(context).typeProvider
            if tp:
               name = ITypeConcept(tp).viewName
        if name:
            if '?' in name:
                name, params = name.split('?', 1)
                ann = self.request.annotations.get('loops.view', {})
                ann['params'] = params
                self.request.annotations['loops.view'] = ann
            # ??? Would it make sense to use a somehow restricted interface
            #     that should be provided by the view like IQuery?
            #viewInterface = getattr(typeAdapter, 'viewInterface', None) or IQuery
            adapter = component.queryMultiAdapter((context, self.request),
                                                  name=name)
            if adapter is not None:
                return adapter
        #elif type provides view: use this
        return self

    def clients(self):
        from loops.browser.node import NodeView  # avoid circular import
        for node in self.context.getClients():
            yield NodeView(node, self.request)

    def getActions(self, category='object', page=None, target=None):
        acts = []
        optKey = 'action.' + category
        actNames = (self.options(optKey) or []) + (self.typeOptions(optKey) or [])
        if actNames:
            acts = list(actions.get(category, actNames,
                                    view=self, page=page, target=target))
        if category in self.actions:
            acts.extend(self.actions[category](self, page, target))
        return acts

    def getObjectActions(self, page=None, target=None):
        acts = ['info']
        acts.extend('state.' + st.statesDefinition for st in self.states)
        if self.globalOptions('organize.allowSendEmail'):
            acts.append('send_email')
        return actions.get('object', acts, view=self, page=page, target=target)

    actions = dict(object=getObjectActions)

    def checkAction(self, name, category, target):
        if name in (self.typeOptions('hide_action.' + category) or []):
            return False
        return super(ConceptView, self).checkAction(name, category, target)

    @Lazy
    def workItems(self):
        return component.getMultiAdapter((self.context, self.request),
                                         name='taskworkitems.html')


class ConceptRelationView(ConceptView, BaseRelationView):

    __init__ = BaseRelationView.__init__

    getData = BaseRelationView.getData


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
            cToken = parts[0]
            if len(parts) > 1:
                relToken = parts[1]
            concept = self.loopsRoot.loopsTraverse(cToken)
            if action == 'assign':
                assignAs = request.get('assignAs', 'child')
                predicate = request.get('predicate') or None
                order = int(request.get('order') or 0)
                relevance = float(request.get('relevance') or 1.0)
                if predicate:
                    predicate = removeSecurityProxy(
                                    self.loopsRoot.loopsTraverse(predicate))
                if assignAs == 'child':
                    self.context.assignChild(removeSecurityProxy(concept), predicate,
                                             order, relevance)
                elif assignAs == 'parent':
                    self.context.assignParent(removeSecurityProxy(concept), predicate,
                                             order, relevance)
                elif assignAs == 'resource':
                    self.context.assignResource(removeSecurityProxy(concept), predicate,
                                             order, relevance)
                else:
                    raise(BadRequest, 'Illegal assignAs parameter: %s.' % assignAs)
            elif action in( 'remove',):
                predicate = self.loopsRoot.loopsTraverse(relToken)
                qualifier = request.get('qualifier')
                if 'form.button.submit' in request:
                    if predicate == self.typePredicate:
                        continue
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
                elif 'form.button.change_relations' in request:
                    self.changeRelation(concept, predicate, qualifier,
                                        request.get('order.' + token),
                                        request.get('relevance.' + token))
            else:
                    raise(BadRequest, 'Illegal action: %s.' % action)
        return True

    def changeRelation(self, target, predicate, qualifier, order, relevance):
        methodNames = dict(parents='getParentRelations',
                           children='getChildRelations',
                           resources='getResourceRelations',
                           concepts='getConceptRelations')
        method = getattr(self.context, methodNames[qualifier])
        for r in method([predicate], target):
            r.order = int(order or 0)
            r.relevance = float(relevance or 1.0)

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
        elif IResource.providedBy(concept):
            concept.resourceType = type.typeProvider
        notify(ObjectCreatedEvent(concept))
        notify(ObjectModifiedEvent(concept))
        assignAs = self.request.get('assignAs', 'child')
        predicate = request.get('create.predicate') or None
        if predicate:
            predicate = removeSecurityProxy(
                            self.loopsRoot.loopsTraverse(predicate))
        order = int(request.get('create.order') or 0)
        relevance = float(request.get('create.relevance') or 1.0)
        if assignAs == 'child':
            self.context.assignChild(concept, predicate, order, relevance)
        elif assignAs == 'parent':
            self.context.assignParent(concept, predicate, order, relevance)
        elif assignAs == 'resource':
            self.context.assignResource(concept, predicate, order, relevance)
        elif assignAs == 'concept':
            self.context.assignConcept(concept, predicate, order, relevance)
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
            cat = component.getUtility(ICatalog)
            result = cat.searchResults(**criteria)
            # TODO: can this be done in a faster way?
            result = [r for r in result if r.getLoopsRoot() == self.loopsRoot]
        else:
            result = self.loopsRoot.getConceptManager().values()
        if searchType == 'none':
            result = [r for r in result if r.conceptType is None]
        result = sorted(result, key=lambda x: x.title)
        return self.viewIterator(result)

    def predicates(self):
        preds = PredicateSourceList(self.context)
        terms = component.getMultiAdapter((preds, self.request), ITerms)
        for pred in preds:
            yield terms.getTerm(pred)


# query views

class ListChildren(ConceptView):

    @Lazy
    def macro(self):
        return concept_macros.macros['list_children']

