#
#  Copyright (c) 2014 Helmut Merz helmutm@cy55.de
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
Classes for form presentation and processing.
"""

from urllib import urlencode
from zope.app.container.contained import ObjectRemovedEvent
from zope import component, interface, schema
from zope.component import adapts
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.container.interfaces import INameChooser
from zope.app.container.contained import ObjectAddedEvent
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.contenttype import guess_content_type
from zope.publisher.browser import FileUpload
from zope.publisher.interfaces import BadRequest
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.security.proxy import isinstance, removeSecurityProxy
from zope.traversing.api import getName, getParent

from cybertools.ajax import innerHtml
from cybertools.browser.form import FormController
from cybertools.browser.view import popupTemplate
from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.grid.field import grid_macros
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.composer.schema.browser.common import schema_macros, schema_edit_macros
from cybertools.composer.schema.schema import FormState
from cybertools.meta.interfaces import IOptions
from cybertools.stateful.interfaces import IStateful
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.util.format import toUnicode
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.common import adapted
from loops.concept import Concept, ConceptRelation, ResourceRelation
from loops.interfaces import IConcept, IConceptSchema
from loops.interfaces import IResource, IResourceManager, IDocument
from loops.interfaces import IFile, IExternalFile, INote, ITextDocument
from loops.i18n.browser import I18NView
from loops.organize.personal.browser.filter import FilterView
from loops.query import ConceptQuery, IQueryConcept
from loops.resource import Resource
from loops.schema.field import relation_macros
from loops.security.common import canAccessObject, canListObject, canWriteObject
from loops.type import ITypeConcept, ConceptTypeInfo
from loops import util
from loops.util import _
from loops.versioning.interfaces import IVersionable


# delete object

class DeleteObject(NodeView):

    isTopLevel = True

    def __call__(self):
        # todo: check permission; check security code
        form = self.request.form
        obj = util.getObjectForUid(form['uid'])
        container = getParent(obj)
        notify(ObjectRemovedEvent(obj))
        del container[getName(obj)]
        message = 'The object requested has been deleted.'
        params = [('loops.message', message.encode('UTF-8'))]
        nextUrl = '%s?%s' % (self.request.URL[-1], urlencode(params))
        return self.request.response.redirect(nextUrl)


# forms

class ObjectForm(NodeView):
    """ Abstract base class for resource or concept forms using Dojo dialog.
    """

    template = ViewPageTemplateFile('form_macros.pt')
    customMacro = None
    formState = FormState()     # dummy, don't update!
    isInnerHtml = True
    isPopup = False
    showAssignments = True

    def checkPermissions(self):
        obj = self.target
        if obj is None:
            obj = self.containerext
        return canWriteObject(obj)

    @Lazy
    def target(self):
        return self.virtualTargetObject or self.context

    @Lazy
    def contextInfo(self):
        return dict(view=self, context=getName(self.context),
                               target=getName(self.target))

    def closeAction(self, submit=False):
        if self.isPopup:
            if submit:
                return ("xhrSubmitPopup('dialog_form', '%s'); return false"
                        % (self.request.URL))
            else:
                return 'window.close()'
        if self.isInnerHtml:
            return "return closeDialog(%s);" % (submit and 'true' or 'false')
        return ''

    @Lazy
    def item(self):
        # show this view on the page instead of the node's view
        return self

    @Lazy
    def adapted(self):
        return adapted(self.target, self.languageInfo)

    @Lazy
    def typeInterface(self):
        return IType(self.target).typeInterface or ITextDocument

    def getFieldRenderers(self):
        renderers = dict(schema_macros.macros)
        # replace HTML edit widget with Dojo Editor
        renderers['input_html'] = self.template.macros['input_html']
        renderers['input_grid'] = grid_macros.macros['input_grid']
        renderers['input_records'] = grid_macros.macros['input_records']
        renderers['input_relationset'] = relation_macros.macros['input_relationset']
        renderers['input_relation'] = relation_macros.macros['input_relation']
        return renderers

    @Lazy
    def fieldRenderers(self):
        return self.getFieldRenderers()

    @Lazy
    def fieldEditRenderers(self):
        return schema_edit_macros.macros

    @Lazy
    def schema(self):
        schemaFactory = ISchemaFactory(self.adapted)
        return schemaFactory(self.typeInterface, manager=self,
                             request=self.request)

    @Lazy
    def fields(self):
        return [f for f in self.schema.fields if not f.readonly]

    @Lazy
    def data(self):
        return self.getData()

    def getData(self):
        instance = self.instance
        data = instance.applyTemplate(mode='edit')
        form = self.request.form
        for k, v in data.items():
            #overwrite data with values from request.form
            if k in self.request.form:
                data[k] = toUnicode(form[k])
        return data

    @Lazy
    def instance(self):
        instance = IInstance(self.adapted)
        instance.template = self.schema
        instance.view = self
        return instance

    def __call__(self):
        if self.isInnerHtml:
            self.checkLanguage()
            response = self.request.response
            #response.setHeader('Content-Type', 'text/html; charset=UTF-8')
            response.setHeader('Expires', 'Sat, 1 Jan 2000 00:00:00 GMT')
            response.setHeader('Pragma', 'no-cache')
            return innerHtml(self)
        else:
            return super(ObjectForm, self).__call__()

    @Lazy
    def defaultPredicate(self):
        return self.loopsRoot.getConceptManager().getDefaultPredicate()

    @Lazy
    def defaultPredicateUid(self):
        return util.getUidForObject(self.defaultPredicate)

    @Lazy
    def typeManager(self):
        return ITypeManager(self.target)

    @Lazy
    def presetTypesForAssignment(self):
        types = list(self.typeManager.listTypes(include=('assign',)))
        assigned = [r.context.conceptType for r in self.assignments]
        types = [t for t in types if t.typeProvider not in assigned]
        return [dict(title=t.title, token=t.tokenForSearch) for t in types]

    def conceptsForType(self, token):
        result = ConceptQuery(self).query(type=token)
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result.sort(key=lambda x: x.title)
        noSelection = dict(token='none', title=u'not selected')
        predicateUid = self.defaultPredicateUid
        return ([noSelection] +
                [dict(title=o.title,
                      token='%s:%s' % (util.getUidForObject(o), predicateUid))
                 for o in result])


class EditObjectForm(ObjectForm):

    title = _(u'Edit Resource')
    form_action = 'edit_resource'
    dialog_name = 'edit'

    @Lazy
    def macro(self):
        return self.template.macros['edit']

    @property
    def assignments(self):
        for c in self.target.getConceptRelations():
            r = ConceptRelationView(c, self.request)
            if r.isProtected:
                continue
            yield r


class EditConceptForm(EditObjectForm):

    isInnerHtml = True

    title = _(u'Edit Concept')
    form_action = 'edit_concept'

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'editConcept')

    @Lazy
    def typeInterface(self):
        return IType(self.target).typeInterface or IConceptSchema

    @property
    def assignments(self):
        for c in self.target.getParentRelations():
            r = ConceptRelationView(c, self.request)
            if r.isProtected or r.isHidden(r.relation):
                continue
            if r.context != self.target:
                yield r


class EditConceptPage(EditConceptForm):

    isInnerHtml = False

    def setupController(self):
        super(EditConceptPage, self).setupController()
        self.registerDojoFormAll()

    def getActions(self, category='object', page=None, target=None):
        return []


class CreateObjectForm(ObjectForm):

    defaultTitle = u'Create Resource, Type = '
    form_action = 'create_resource'
    dialog_name = 'create'

    @property
    def macro(self): return self.template.macros['create']

    @Lazy
    def fixedType(self):
        return self.request.form.get('fixed_type')

    @Lazy
    def defaultTypeToken(self):
        return (self.controller.params.get('form.create.defaultTypeToken')
                or '.loops/concepts/textdocument')

    @Lazy
    def typeToken(self):
        return self.request.form.get('form.type') or self.defaultTypeToken

    @Lazy
    def title(self):
        if self.fixedType:
            #return _(u'Create %s') % self.typeConcept.title
            return _(u'Create $type', 
                     mapping=dict(type=self.typeConcept.title))
        else:
            return _(self.defaultTitle)

    @Lazy
    def typeConcept(self):
        typeToken = self.typeToken
        if typeToken:
            return self.loopsRoot.loopsTraverse(typeToken)

    @Lazy
    def adapted(self):
        ad = self.typeInterface(Resource())
        ad.storageName = 'unknown'  # hack for file objects: don't try to retrieve data
        ad.__type__ = adapted(self.typeConcept)
        return ad

    @Lazy
    def instance(self):
        instance = IInstance(self.adapted)
        instance.template = self.schema
        instance.view = self
        return instance

    @Lazy
    def typeInterface(self):
        tc = self.typeConcept
        if tc:
            return removeSecurityProxy(ITypeConcept(tc).typeInterface)
        else:
            return ITextDocument

    @property
    def assignments(self):
        target = self.virtualTargetObject
        if self.maybeAssignedAsParent(target):
            rv = ConceptRelationView(ResourceRelation(target, None), self.request)
            return (rv,)
        if IResource.providedBy(target):
            return tuple(ConceptRelationView(ResourceRelation(p, None), self.request)
                            for p in target.getConcepts()
                            if self.maybeAssignedAsParent(p))
        return ()

    def maybeAssignedAsParent(self, obj):
        if not IConcept.providedBy(obj):
            return False
        qualifiers = IType(obj).qualifiers
        if (obj.conceptType == self.conceptManager.getTypeConcept()
                and not 'assign' in qualifiers):
            return False
        if 'noassign' in qualifiers:
            return False
        adap = adapted(obj)
        if 'noassign' in getattr(adap, 'options', []):
            return False
        return True


class CreateObjectPopup(CreateObjectForm):

    isInnerHtml = False
    isPopup = True
    nextUrl = ''    # no redirect upon submit

    def update(self):
        show = super(ObjectForm, self).update()
        if not show:
            return False
        self.registerDojo()
        cm = self.controller.macros
        cm.register('css', identifier='popup.css', resourceName='popup.css',
                    media='all', priority=90) #, position=4)
        jsCall = ('dojo.require("dojo.parser");'
                  'dojo.require("dijit.form.FilteringSelect");'
                  'dojo.require("dojox.data.QueryReadStore");')
        cm.register('js-execute', jsCall, jsCall=jsCall)
        return True

    def pageBody(self):
        return popupTemplate(self)


class CreateConceptForm(CreateObjectForm):

    defaultTitle = u'Create Concept, Type = '
    form_action = 'create_concept'
    inner_form = 'inner_concept_form.html'
    qualifier = 'concept'

    @Lazy
    def defaultTypeToken(self):
        return None

    def getTypesVocabulary(self, include=None):
        types = []
        if include and 'subtype' in include:
            include = list(include)
            include.remove('subtype')
            parentType = self.target.conceptType
            subtypePred = self.conceptManager['issubtype']
            tconcepts = (self.target.getChildren([subtypePred]) +
                            parentType.getChildren([subtypePred]))
            types = [dict(token=ConceptTypeInfo(t).token, title=t.title)
                        for t in tconcepts]
        if self.defaultTypeToken is None and types:
            self.defaultTypeToken = types[0]['token']
        if include or include is None:
            return util.KeywordVocabulary(types + self.listTypes(include, ('hidden',)))
        return util.KeywordVocabulary(types)

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'createConcept')

    @Lazy
    def adapted(self):
        c = Concept()
        ti = self.typeInterface
        if ti is None:
            return c
        ad = ti(c)
        ad.__is_dummy__ = True
        ad.__type__ = adapted(self.typeConcept)
        return ad

    @Lazy
    def instance(self):
        instance = IInstance(self.adapted)
        instance.template = self.schema
        instance.view = self
        return instance

    @Lazy
    def typeInterface(self):
        if self.typeConcept:
            ti = ITypeConcept(self.typeConcept).typeInterface
            if ti is not None:
                return removeSecurityProxy(ti)
        return IConceptSchema

    @property
    def assignments(self):
        target = self.virtualTargetObject
        if self.maybeAssignedAsParent(target):
            rv = ConceptRelationView(ConceptRelation(target, None), self.request)
            return (rv,)
        return ()


class CreateConceptPage(CreateConceptForm):

    isInnerHtml = False

    def setupController(self):
        super(CreateConceptPage, self).setupController()
        self.registerDojoFormAll()

    def getActions(self, category='object', page=None, target=None):
        return []

    @Lazy
    def nextUrl(self):
        return self.getUrlForTarget(self.virtualTargetObject)


class InnerForm(CreateObjectForm):

    @property
    def macro(self):
        return self.fieldRenderers['fields']


class InnerConceptForm(CreateConceptForm):

    @property
    def macro(self):
        return self.fieldRenderers['fields']


class InnerConceptEditForm(EditConceptForm):

    @property
    def macro(self):
        return self.fieldRenderers['fields']


# processing form input

class EditObject(FormController, I18NView):
    """ Note that ``self.context`` of this adapter may be different from
        ``self.object``, the object it acts upon, e.g. when this object
        is created during the update processing.
    """

    prefix = 'form.'
    conceptPrefix = 'assignments.'

    def __init__(self, context, request):
        super(EditObject, self).__init__(context, request)
        try:
            if not self.checkPermissions():
                raise Unauthorized(str(self.contextInfo))
        except ForbiddenAttribute:  # ignore when testing
            pass

    def checkPermissions(self):
        return canWriteObject(self.target)

    @Lazy
    def contextInfo(self):
        return dict(formcontroller=self, view=self.view, target=getName(self.target))

    @Lazy
    def target(self):
        targetUid = self.request.form.get('targetUid')
        if targetUid:
            return self.view.getObjectForUid(targetUid)
        return self.view.virtualTargetObject or self.context

    @Lazy
    def adapted(self):
        return adapted(self.object, self.languageInfoForUpdate)

    @Lazy
    def typeInterface(self):
        return IType(self.object).typeInterface or ITextDocument

    @Lazy
    def schema(self):
        schemaFactory = ISchemaFactory(self.adapted)
        return schemaFactory(self.typeInterface, manager=self,
                             request=self.request)

    @Lazy
    def fields(self):
        return self.schema.fields

    @Lazy
    def instance(self):
        instance = component.getAdapter(self.adapted, IInstance, name='editor')
        instance.template = self.schema
        instance.view = self.view
        return instance

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def update(self):
        # create new version if necessary
        target = self.target
        obj = self.checkCreateVersion(target)
        if obj != target:
            # make sure new version is used by the view
            self.view.virtualTargetObject = obj
            viewAnnotations = self.request.annotations.setdefault('loops.view', {})
            viewAnnotations['target'] = obj
        self.object = obj
        formState = self.updateFields()
        self.view.formState = formState
        # TODO: error handling
        url = self.view.nextUrl
        if url is None:
            url = self.view.virtualTargetUrl + '?version=this'
        if url:
            self.request.response.redirect(url)
        return False

    def updateFields(self):
        obj = self.object
        form = self.request.form
        instance = self.instance
        formState = instance.applyTemplate(data=form, fieldHandlers=self.fieldHandlers)
        self.selected = []
        self.predicates = []
        self.old = []
        stateKeys = []
        for k in form.keys():
            if k.startswith(self.prefix):
                fn = k[len(self.prefix):]
                value = form[k]
                if fn.startswith(self.conceptPrefix) and value:
                    self.collectConcepts(fn[len(self.conceptPrefix):], value)
            if k.startswith('state.'):
                stateKeys.append(k)
        self.collectAutoConcepts()
        #if self.old or self.selected:
        self.assignConcepts(obj)
        for k in stateKeys:
            self.updateState(k)
        notify(ObjectModifiedEvent(obj))
        return formState

    def updateState(self, key):
        trans = self.request.form.get(key, '-')
        if trans == '-':
            return
        stdName = key[len('state.'):]
        stf = component.getAdapter(self.object, IStateful, name=stdName)
        stf.doTransition(trans)

    def handleFileUpload(self, context, value, fieldInstance, formState):
        """ Special handler for fileupload fields;
            value is a FileUpload instance.
        """
        filename = getattr(value, 'filename', '')
        if filename:    # ignore if no filename present - no file uploaded
            value = value.read()
            contentType = guess_content_type(filename, value[:100])
            if contentType:
                ct = contentType[0]
                self.request.form['form.contentType'] = ct
                context.contentType = ct
            setattr(context, fieldInstance.name, value)
            context.localFilename = filename

    @property
    def fieldHandlers(self):
        return dict(fileupload=self.handleFileUpload)

    def collectConcepts(self, fieldName, value):
        if self.old is None:
            self.old = []
        for v in value:
            if fieldName == 'old':
                self.old.append(v)
            elif fieldName == 'selected' and v not in self.selected:
                self.selected.append(v)
            elif fieldName == 'predicates' and v not in self.predicates:
                self.predicates.append(v)

    def collectAutoConcepts(self):
        pass

    def assignConcepts(self, obj):
        for v in self.old:
            if v not in self.selected:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                self.deassignConcept(obj, concept, [predicate])
        for idx, v in enumerate(self.selected):
            if v != 'none' and v not in self.old:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                if len(self.predicates) > idx:  # predefined types + predicates
                    predicate = self.view.conceptManager[self.predicates[idx]]
                else:
                    predicate = util.getObjectForUid(p)
                exists = self.getConceptRelations(obj, [p], concept)
                if not exists:
                    self.assignConcept(obj, concept, predicate)

    def getConceptRelations(self, obj, predicates, concept):
        return obj.getConceptRelations(predicates=predicates, concept=concept)

    def assignConcept(self, obj, concept, predicate):
        obj.assignConcept(concept, predicate)

    def deassignConcept(self, obj, concept, predicates):
        obj.deassignConcept(concept, predicates)

    def checkCreateVersion(self, obj):
        form = self.request.form
        versionable = IVersionable(obj)
        notVersioned = bool(form.get('version.not_versioned'))
        if notVersioned != versionable.notVersioned:
            versionable.notVersioned = notVersioned
        if not notVersioned and form.get('version.create'):
            level = int(form.get('version.level', 0))
            version = versionable.createVersion(level)
            notify(ObjectCreatedEvent(version))
            return version
        return obj


class CreateObject(EditObject):

    factory = Resource
    defaultTypeToken = '.loops/concepts/textdocument'

    @Lazy
    def container(self):
        return self.loopsRoot.getResourceManager()

    def getNameFromData(self):
        data = self.request.form.get('data')
        if data and isinstance(data, FileUpload):
            name = getattr(data, 'filename', None)
            # strip path from IE uploads:
            if '\\' in name:
                name = name.rsplit('\\', 1)[-1]
        else:
            name = None
        return name

    def update(self):
        form = self.request.form
        container = self.container
        title = form.get('title')
        if not title:
            raise BadRequest('Title field is empty')
        obj = self.factory(title)
        name = self.getNameFromData()
        # TODO: validate fields
        name = INameChooser(container).chooseName(name, obj)
        container[name] = obj
        tc = form.get('form.type') or self.defaultTypeToken
        obj.setType(self.loopsRoot.loopsTraverse(tc))
        notify(ObjectCreatedEvent(obj))
        #notify(ObjectAddedEvent(obj))
        self.object = self.view.object = obj
        formState = self.updateFields() # TODO: suppress validation
        self.view.formState = formState
        # TODO: error handling
        url = self.view.nextUrl
        if url is None:
            self.request.response.redirect(self.view.request.URL)
        if url:
            self.request.response.redirect(url)
        return False


class EditConcept(EditObject):

    @Lazy
    def typeInterface(self):
        return IType(self.object).typeInterface or IConceptSchema

    def getConceptRelations(self, obj, predicates, concept):
        return obj.getParentRelations(predicates=predicates, parent=concept)

    def assignConcept(self, obj, concept, predicate):
        if IOptions(adapted(concept.conceptType)).children_append:
            sibRelations = concept.getChildRelations()
            if sibRelations:
                maxOrder = max([r.order for r in sibRelations])
                if maxOrder > 0:
                    return obj.assignParent(concept, predicate, 
                                            order=maxOrder+1)
        obj.assignParent(concept, predicate)

    def deassignConcept(self, obj, concept, predicates):
        obj.deassignParent(concept, predicates)

    def update(self):
        self.object = self.view.item.target
        formState = self.updateFields()
        self.view.formState = formState
        # TODO: error handling
        if formState.severity > 0:
            return True
        self.request.response.redirect(self.view.virtualTargetUrl)
        return False


class CreateConcept(EditConcept, CreateObject):

    factory = Concept
    defaultTypeToken = '.loops/concepts/topic'

    @Lazy
    def container(self):
        return self.loopsRoot.getConceptManager()

    def getNameFromData(self):
        return None

    def update(self):
        return CreateObject.update(self)

