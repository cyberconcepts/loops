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
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent

from zope.app.container.interfaces import INameChooser
from zope.app.container.contained import NameChooser
from zope.app.form.browser.textwidgets import FileWidget, TextAreaWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.contenttype import guess_content_type
from zope.formlib.form import Form, EditForm, FormFields
from zope.publisher.browser import FileUpload
from zope.publisher.interfaces import BadRequest
from zope.security.proxy import isinstance, removeSecurityProxy

from cybertools.ajax import innerHtml
from cybertools.browser.form import FormController
from cybertools.typology.interfaces import IType, ITypeManager
from loops.concept import ResourceRelation
from loops.interfaces import IConcept, IResourceManager, IDocument
from loops.interfaces import IFile, IExternalFile, INote, ITextDocument
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.query import ConceptQuery
from loops.resource import Resource
from loops.type import ITypeConcept
from loops import util
from loops.util import _
from loops.versioning.interfaces import IVersionable


# special widgets

class UploadWidget(FileWidget):

    def _toFieldValue(self, input):
        # not used at the moment as the context object is updated
        # via EditObject.updateFields()
        fn = getattr(input, 'filename', '') # zope.publisher.browser.FileUpload
        self.request.form['filename'] = fn
        if input:
            self.request.form['_tempfilename'] = input.headers.get('_tempfilename')
        # f = self.context
        # f.extfiledata = tempfilename  # provide for rename
        if fn:
            contentType = guess_content_type(fn)
            if contentType:
                request.form['form.contentType'] = contentType
        return super(UploadWidget, self)._toFieldValue(input)


# forms

class ObjectForm(NodeView):

    template = ViewPageTemplateFile('form_macros.pt')

    _isSetUp = False

    def __init__(self, context, request):
        super(ObjectForm, self).__init__(context, request)

    def setUp(self):
        if self._isSetUp:
            return
        self.setUpWidgets()
        desc = self.widgets.get('description')
        if desc:
            desc.height = 2
        if self.typeInterface in widgetControllers:
            wc = widgetControllers[self.typeInterface](self.context, self.request)
            wc.modifyWidgetSetup(self.widgets)
        self._isSetUp = True

    def __call__(self):
        response = self.request.response
        response.setHeader('Expires', 'Sat, 1 Jan 2000 00:00:00 GMT')
        response.setHeader('Pragma', 'no-cache')
        return innerHtml(self)

    @Lazy
    def defaultPredicate(self):
        return self.loopsRoot.getConceptManager().getDefaultPredicate()

    @Lazy
    def defaultPredicateUid(self):
        return util.getUidForObject(self.defaultPredicate)

    @Lazy
    def typeManager(self):
        return ITypeManager(self.context)

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


class WidgetController(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def modifyFormFields(self, formFields):
        return formFields

    def modifyWidgetSetup(self, widgets):
        pass


class NoteWidgetController(WidgetController):

    def modifyFormFields(self, formFields):
        return formFields.omit('description')

    def modifyWidgetSetup(self, widgets):
        widgets['data'].height = 5


class FileWidgetController(WidgetController):

    def modifyFormFields(self, formFields):
        if self.request.principal.id == 'rootadmin':
            return formFields
        return formFields.omit('contentType')


widgetControllers = {
    INote: NoteWidgetController,
    IFile: FileWidgetController,
    IExternalFile: FileWidgetController,
}


class EditObjectForm(ObjectForm, EditForm):

    @property
    def macro(self): return self.template.macros['edit']

    title = _(u'Edit Resource')
    form_action = 'edit_resource'
    dialog_name = 'edit'

    def __init__(self, context, request):
        super(EditObjectForm, self).__init__(context, request)
        self.url = self.url # keep virtual target URL
        self.context = self.virtualTargetObject

    @Lazy
    def typeInterface(self):
        return IType(self.context).typeInterface or IDocument

    @property
    def form_fields(self):
        ff = FormFields(self.typeInterface)
        if self.typeInterface in widgetControllers:
            wc = widgetControllers[self.typeInterface](self.context, self.request)
            ff = wc.modifyFormFields(ff)
        return ff

    @property
    def assignments(self):
        for c in self.context.getConceptRelations():
            r = ConceptRelationView(c, self.request)
            if r.isProtected: continue
            yield r


class CreateObjectForm(ObjectForm, Form):

    @property
    def macro(self): return self.template.macros['create']

    title = _(u'Create Resource, Type = ')
    form_action = 'create_resource'
    dialog_name = 'create'

    @property
    def form_fields(self):
        typeToken = self.request.get('form.type')
        if typeToken:
            t = self.loopsRoot.loopsTraverse(typeToken)
            ifc = removeSecurityProxy(ITypeConcept(t).typeInterface)
        else:
            #ifc = INote
            ifc = ITextDocument
        self.typeInterface = ifc
        ff = FormFields(ifc)
        #ff['data'].custom_widget = UploadWidget
        if self.typeInterface in widgetControllers:
            wc = widgetControllers[self.typeInterface](self.context, self.request)
            ff = wc.modifyFormFields(ff)
        return ff

    @property
    def assignments(self):
        target = self.virtualTargetObject
        if (IConcept.providedBy(target) and
            target.conceptType != self.loopsRoot.getConceptManager().getTypeConcept()):
            rv = ConceptRelationView(ResourceRelation(target, None), self.request)
            return (rv,)
        return ()


class InnerForm(CreateObjectForm):

    @property
    def macro(self): return self.template.macros['fields']


# processing form input

class EditObject(FormController):

    prefix = 'form.'
    conceptPrefix = 'assignments.'

    old = None
    selected = None

    def update(self):
        # create new version if necessary
        target = self.view.virtualTargetObject
        obj = self.checkCreateVersion(target)
        if obj != target:
            # make sure new version is used by the view
            self.view.virtualTargetObject = obj
            self.request.annotations['loops.view']['target'] = obj
        errors = self.updateFields(obj)
        if errors:
            self.view.setUp()
            for fieldName, message in errors.items():
                self.view.widgets[fieldName].error = message
            return True
        self.request.response.redirect(self.view.virtualTargetUrl + '?version=this')
        return False

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def updateFields(self, obj):
        errors = {}
        form = self.request.form
        ti = IType(obj).typeInterface
        if ti is not None:
            adapted = ti(obj)
        else:
            adapted = obj
        for k in form.keys():
            # TODO: use self.view.form_fields
            if k.startswith(self.prefix):
                fn = k[len(self.prefix):]
                if fn in ('action', 'type', 'data.used') or fn.endswith('-empty-marker'):
                    continue
                value = form[k]
                if fn.startswith(self.conceptPrefix) and value:
                    self.collectConcepts(fn[len(self.conceptPrefix):], value)
                else:
                    if not value and fn == 'data' and IFile.providedBy(adapted):
                        # empty file data - don't change
                        continue
                    if isinstance(value, FileUpload):
                        filename = getattr(value, 'filename', '')
                        value = value.read()
                        if filename:
                            #self.request.form['filename'] = filename
                            contentType = guess_content_type(filename, value[:100])
                            if contentType:
                                ct = contentType[0]
                                self.request.form['form.contentType'] = ct
                                adapted.contentType = ct
                            adapted.localFilename = filename
                    if fn == 'title' and not value:
                        # TODO: provide general validation mechanism
                        errors[fn] = 'Field %s must not be empty' % fn
                    else:
                        # TODO: provide unmarshalling depending on field type
                        setattr(adapted, fn, value)
        if self.old or self.selected:
            self.assignConcepts(obj)
        notify(ObjectModifiedEvent(obj))
        return errors

    def collectConcepts(self, fieldName, value):
        if self.old is None: self.old = []
        if self.selected is None: self.selected = []
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
                obj.deassignConcept(concept, [predicate])
        for v in self.selected:
            if v != 'none' and v not in self.old:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                exists = obj.getConceptRelations(predicates=[p], concept=concept)
                if not exists:
                    obj.assignConcept(concept, predicate)

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

    def update(self):
        form = self.request.form
        container = self.loopsRoot.getResourceManager()
        title = form.get('form.title')
        if not title:
            raise BadRequest('Title field is empty')
        obj = Resource(title)
        data = form.get('form.data')
        if data and isinstance(data, FileUpload):
            name = getattr(data, 'filename', None)
            # strip path from IE uploads:
            if '\\' in name:
                name = name.rsplit('\\', 1)[-1]
        else:
            name = None
        name = INameChooser(container).chooseName(name, obj)
        container[name] = obj
        tc = form.get('form.type') or '.loops/concepts/note'
        obj.resourceType = self.loopsRoot.loopsTraverse(tc)
        notify(ObjectCreatedEvent(obj))
        self.updateFields(obj)
        self.request.response.redirect(self.view.virtualTargetUrl)
        return False

