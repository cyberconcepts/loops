#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope import component, interface, schema
from zope.component import adapts
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent

from zope.app.container.interfaces import INameChooser
from zope.app.container.contained import NameChooser
from zope.app.form.browser.textwidgets import FileWidget, TextAreaWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.contenttype import guess_content_type
#from zope.formlib.form import Form, EditForm, FormFields
from zope.publisher.browser import FileUpload
from zope.publisher.interfaces import BadRequest
from zope.security.proxy import isinstance, removeSecurityProxy

from cybertools.ajax import innerHtml
from cybertools.browser.form import FormController
from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.composer.schema.browser.common import schema_macros, schema_edit_macros
from cybertools.composer.schema.schema import FormState
from cybertools.typology.interfaces import IType, ITypeManager
from loops.common import adapted
from loops.concept import Concept, ConceptRelation, ResourceRelation
from loops.interfaces import IConcept, IConceptSchema, IResourceManager, IDocument
from loops.interfaces import IFile, IExternalFile, INote, ITextDocument
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.i18n.browser import I18NView
from loops.query import ConceptQuery
from loops.resource import Resource
from loops.type import ITypeConcept
from loops import util
from loops.util import _
from loops.versioning.interfaces import IVersionable


# forms

class ObjectForm(NodeView):
    """ Abstract base class for resource or concept forms using Dojo dialog.
    """

    template = ViewPageTemplateFile('form_macros.pt')
    customMacro = None
    formState = FormState()     # dummy, don't update!
    isInnerHtml = True

    def __init__(self, context, request):
        super(ObjectForm, self).__init__(context, request)
        # target is the object the view acts upon - this is not necessarily
        # the same object as the context (the object the view was created for)
        self.target = context

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

    @Lazy
    def fieldRenderers(self):
        return schema_macros.macros

    @Lazy
    def fieldEditRenderers(self):
        return schema_edit_macros.macros

    @Lazy
    def schema(self):
        #ti = self.typeInterface or Interface #IConcept
        ti = self.typeInterface or IConceptSchema
        schemaFactory = component.getAdapter(self.adapted, ISchemaFactory)
        return schemaFactory(ti, manager=self, request=self.request)

    @Lazy
    def fields(self):
        return self.schema.fields

    @Lazy
    def data(self):
        instance = self.instance
        instance.template = self.schema
        data = instance.applyTemplate(mode='edit')
        for k, v in data.items():
            #overwrite data with values from request.form
            if k in self.request.form:
                data[k] = form[k]
        return data

    @Lazy
    def instance(self):
        return IInstance(self.adapted)

    def __call__(self):
        if self.isInnerHtml:
            response = self.request.response
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
        noSelection = dict(token='none', title=u'not selected')
        result = sorted(ConceptQuery(self).query(type=token), key=lambda x: x.title)
        predicateUid = self.defaultPredicateUid
        return ([noSelection] +
                [dict(title=o.title,
                      token='%s:%s' % (util.getUidForObject(o), predicateUid))
                 for o in result])


class EditObjectForm(ObjectForm):

    @Lazy
    def macro(self):
        return self.template.macros['edit']

    title = _(u'Edit Resource')
    form_action = 'edit_resource'
    dialog_name = 'edit'

    def __init__(self, context, request):
        super(EditObjectForm, self).__init__(context, request)
        #self.url = self.url # keep virtual target URL (???)
        self.target = self.virtualTargetObject

    @property
    def assignments(self):
        for c in self.target.getConceptRelations():
            r = ConceptRelationView(c, self.request)
            if r.isProtected: continue
            yield r


class EditConceptForm(EditObjectForm):

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
            if not r.isProtected and r.context != self.target:
                yield r


class CreateObjectForm(ObjectForm):

    @property
    def macro(self): return self.template.macros['create']

    defaultTitle = u'Create Resource, Type = '
    form_action = 'create_resource'
    dialog_name = 'create'

    @Lazy
    def title(self):
        if self.request.form.get('fixed_type'):
            return _(u'Create %s' % self.typeConcept.title)
        else:
            return _(self.defaultTitle)

    @Lazy
    def typeConcept(self):
        typeToken = self.request.get('form.type')
        if typeToken:
            return self.loopsRoot.loopsTraverse(typeToken)

    @Lazy
    def adapted(self):
        return self.typeInterface(Resource())

    @Lazy
    def instance(self):
        return IInstance(Resource())

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
        if (IConcept.providedBy(target) and
                target.conceptType !=
                    self.loopsRoot.getConceptManager().getTypeConcept()):
            rv = ConceptRelationView(ResourceRelation(target, None), self.request)
            return (rv,)
        return ()


class CreateConceptForm(CreateObjectForm):

    defaultTitle = u'Create Concept, Type = '
    form_action = 'create_concept'

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'createConcept')

    @Lazy
    def adapted(self):
        ti = self.typeInterface
        if ti is None:
            return Concept()
        return ti(Concept())

    @Lazy
    def instance(self):
        return IInstance(Concept())

    @Lazy
    def typeInterface(self):
        if self.typeConcept:
            return removeSecurityProxy(ITypeConcept(self.typeConcept).typeInterface)

    @property
    def assignments(self):
        target = self.virtualTargetObject
        if (IConcept.providedBy(target) and
                target.conceptType !=
                    self.loopsRoot.getConceptManager().getTypeConcept()):
            rv = ConceptRelationView(ConceptRelation(target, None), self.request)
            return (rv,)
        return ()


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

    old = None
    selected = None

    @Lazy
    def adapted(self):
        return adapted(self.object, self.languageInfo)

    @Lazy
    def typeInterface(self):
        return IType(self.object).typeInterface or ITextDocument

    @Lazy
    def schema(self):
        schemaFactory = component.getAdapter(self.adapted, ISchemaFactory)
        return schemaFactory(self.typeInterface)

    @Lazy
    def fields(self):
        return self.schema.fields

    @Lazy
    def instance(self):
        return component.getAdapter(self.adapted, IInstance, name='editor')

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def update(self):
        # create new version if necessary
        target = self.view.virtualTargetObject
        obj = self.checkCreateVersion(target)
        if obj != target:
            # make sure new version is used by the view
            self.view.virtualTargetObject = obj
            viewAnnotations = self.request.annotations.setdefault('loops.view', {})
            viewAnnotations['target'] = obj
        self.object = obj
        formState = self.updateFields()
        # TODO: error handling
        self.request.response.redirect(self.view.virtualTargetUrl + '?version=this')
        return False

    def updateFields(self):
        obj = self.object
        form = self.request.form
        instance = self.instance
        instance.template = self.schema
        formState = instance.applyTemplate(data=form, fieldHandlers=self.fieldHandlers)
        for k in form.keys():
            if k.startswith(self.prefix):
                fn = k[len(self.prefix):]
                value = form[k]
                if fn.startswith(self.conceptPrefix) and value:
                    self.collectConcepts(fn[len(self.conceptPrefix):], value)
        if self.old or self.selected:
            self.assignConcepts(obj)
        notify(ObjectModifiedEvent(obj))
        return formState

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
        if self.selected is None:
            self.selected = []
        for v in value:
            if fieldName == 'old':
                self.old.append(v)
            elif fieldName == 'selected' and v not in self.selected:
                self.selected.append(v)

    def assignConcepts(self, obj):
        for v in self.old:
            if v not in self.selected:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                self.deassignConcept(obj, concept, [predicate])
        for v in self.selected:
            if v != 'none' and v not in self.old:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
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
        if form.get('version.create'):
            versionable = IVersionable(obj)
            level = int(form.get('version.level', 1))
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
        self.object = obj
        self.updateFields() # TODO: suppress validation
        #self.request.response.redirect(self.view.virtualTargetUrl)
        self.request.response.redirect(self.view.request.URL)
        return False


class EditConcept(EditObject):

    def getConceptRelations(self, obj, predicates, concept):
        return obj.getParentRelations(predicates=predicates, parent=concept)

    def assignConcept(self, obj, concept, predicate):
        obj.assignParent(concept, predicate)

    def deassignConcept(self, obj, concept, predicates):
        obj.deassignParent(concept, predicates)

    def update(self):
        self.object = self.view.virtualTargetObject
        formState = self.updateFields()
        # TODO: error handling
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

