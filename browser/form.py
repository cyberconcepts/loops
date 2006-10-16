#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent

from zope.app.container.interfaces import INameChooser
from zope.app.container.contained import NameChooser
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.form import Form, EditForm, FormFields
from zope.publisher.browser import FileUpload
from zope.publisher.interfaces import BadRequest
from zope.security.proxy import isinstance

from cybertools.ajax import innerHtml
from cybertools.browser.form import FormController
from cybertools.typology.interfaces import IType
from loops.concept import ResourceRelation
from loops.interfaces import IConcept, IResourceManager, INote, IDocument
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.resource import Resource
from loops.type import ITypeConcept
from loops import util
from loops.util import _


# forms

class ObjectForm(NodeView):

    template = ViewPageTemplateFile('form_macros.pt')

    def __init__(self, context, request):
        super(ObjectForm, self).__init__(context, request)

    def setUp(self):
        self.setUpWidgets()
        if self.typeInterface in widgetControllers:
            wc = widgetControllers[self.typeInterface]()
            wc.modifyWidgetSetup(self.widgets)

    def __call__(self):
        response = self.request.response
        response.setHeader('Expires', 'Sat, 1 Jan 2000 00:00:00 GMT')
        response.setHeader('Pragma', 'no-cache')
        return innerHtml(self)

    @Lazy
    def defaultPredicate(self):
        return util.getUidForObject(
                self.loopsRoot.getConceptManager().getDefaultPredicate())


class NoteWidgetController(object):

    def modifyWidgetSetup(self, widgets):
        widgets['data'].height = 5


widgetControllers = {INote: NoteWidgetController}


class EditObjectForm(ObjectForm, EditForm):

    @property
    def macro(self): return self.template.macros['edit']

    title = _(u'Edit Resource')
    form_action = 'edit_resource'
    dialog_name = 'edit'

    @Lazy
    def typeInterface(self):
        return IType(self.context).typeInterface or IDocument

    @property
    def form_fields(self):
        return FormFields(self.typeInterface)

    @property
    def assignments(self):
        for c in self.context.getConceptRelations():
            r = ConceptRelationView(c, self.request)
            if r.isProtected: continue
            yield r

    def __init__(self, context, request):
        super(EditObjectForm, self).__init__(context, request)
        self.context = self.virtualTargetObject


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
            ifc = ITypeConcept(t).typeInterface
        else:
            ifc = INote
        self.typeInterface = ifc
        return FormFields(ifc)

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
        self.updateFields(self.view.virtualTargetObject)
        return True

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def updateFields(self, obj):
        form = self.request.form
        ti = IType(obj).typeInterface
        if ti is not None:
            adapted = IType(obj).typeInterface(obj)
        else:
            adapted = obj
        for k in form.keys():
            if k.startswith(self.prefix):
                fn = k[len(self.prefix):]
                if fn in ('action', 'type', 'data.used') or fn.endswith('-empty-marker'):
                    continue
                value = form[k]
                if fn.startswith(self.conceptPrefix) and value:
                    self.collectConcepts(fn[len(self.conceptPrefix):], value)
                else:
                    if isinstance(value, FileUpload):
                        value = value.read()
                    setattr(adapted, fn, value)
        if self.old or self.selected:
            self.assignConcepts(obj)
        notify(ObjectModifiedEvent(obj))

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
            if v not in self.old:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                exists = obj.getConceptRelations(predicates=[p], concept=concept)
                if not exists:
                    obj.assignConcept(concept, predicate)


class CreateObject(EditObject):

    def update(self):
        form = self.request.form
        obj = Resource()
        container = self.loopsRoot.getResourceManager()
        title = form.get('form.title')
        if not title:
            raise BadRequest('Title field is empty')
        name = INameChooser(container).chooseName(title, obj)
        container[name] = obj
        tc = form.get('form.type') or '.loops/concepts/note'
        obj.resourceType = self.loopsRoot.loopsTraverse(tc)
        notify(ObjectCreatedEvent(obj))
        self.updateFields(obj)
        return True


specialCharacters = {
    '\xc4': 'Ae', '\xe4': 'ae', '\xd6': 'Oe', '\xf6': 'oe',
    '\xdc': 'Ue', '\xfc': 'ue', '\xdf': 'ss'}

class ResourceNameChooser(NameChooser):

    adapts(IResourceManager)

    def chooseName(self, title, obj):
        result = []
        if len(title) > 15:
            words = title.split()
            if len(words) > 1:
                title = '_'.join((words[0], words[-1]))
        for c in title:
            try:
                c = c.encode('ISO8859-15')
            except UnicodeEncodeError:
                continue
            if c in specialCharacters:
                result.append(specialCharacters[c].lower())
                continue
            if ord(c) > 127:
                c = chr(ord(c) & 127)
            if c in ('_., '):
                result.append('_')
            elif not c.isalpha() and not c.isdigit():
                continue
            else:
                result.append(c.lower())
        name = unicode(''.join(result))
        return super(ResourceNameChooser, self).chooseName(name, obj)

