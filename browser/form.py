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
from zope.publisher.interfaces import BadRequest

from cybertools.ajax import innerHtml
from cybertools.browser.form import FormController
from cybertools.typology.interfaces import IType
from loops.interfaces import IResourceManager, INote
from loops.browser.node import NodeView
from loops.resource import Resource
from loops.type import ITypeConcept
from loops import util
from loops.util import _


class ObjectForm(NodeView):

    template = ViewPageTemplateFile('form_macros.pt')

    def __init__(self, context, request):
        super(ObjectForm, self).__init__(context, request)

    def setUp(self):
        self.setUpWidgets()
        self.widgets['data'].height = 3

    def __call__(self):
        return innerHtml(self)


class CreateObjectForm(ObjectForm, Form):

    @property
    def macro(self): return self.template.macros['create']

    title = _(u'Create Resource, Type = ')
    form_action = 'create_resource'

    @property
    def form_fields(self):
        typeToken = self.request.get('form.type')
        if typeToken:
            t = self.loopsRoot.loopsTraverse(typeToken)
            ifc = ITypeConcept(t).typeInterface
        else:
            ifc = INote
        return FormFields(ifc)


class EditObjectForm(ObjectForm, EditForm):

    @property
    def macro(self): return self.template.macros['edit']

    title = _(u'Edit Resource')
    form_action = 'edit_resource'

    @Lazy
    def typeInterface(self):
        return IType(self.context).typeInterface

    @property
    def form_fields(self):
        return FormFields(self.typeInterface)

    def __init__(self, context, request):
        super(EditObjectForm, self).__init__(context, request)
        self.context = self.virtualTargetObject


class InnerForm(ObjectForm):

    @property
    def macro(self): return self.template.macros['fields']


class CreateObject(FormController):

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def update(self):
        prefix = 'form.'
        conceptPrefix = 'concept.'
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
        adapter = IType(obj).typeInterface(obj)
        for k in form.keys():
            if k.startswith(prefix):
                fn = k[len(prefix):]
                if fn in ('action', 'type',) or fn.endswith('-empty-marker'):
                    continue
                value = form[k]
                if fn.startswith(conceptPrefix):
                    self.assignConcepts(obj, fn[len(conceptPrefix):], value)
                else:
                    setattr(adapter, fn, value)
        notify(ObjectCreatedEvent(obj))
        notify(ObjectModifiedEvent(obj))
        return True

    def assignConcepts(self, obj, fieldName, value):
        if value and fieldName == 'search.text_selected':
            concept = util.getObjectForUid(value)
            obj.assignConcept(concept)


class ResourceNameChooser(NameChooser):

    adapts(IResourceManager)

    def chooseName(self, title, obj):
        name = title.replace(' ', '_').lower()
        name = super(ResourceNameChooser, self).chooseName(name, obj)
        return name


class EditObject(FormController):

    @Lazy
    def loopsRoot(self):
        return self.view.loopsRoot

    def update(self):
        prefix = 'form.'
        conceptPrefix = 'concept.'
        form = self.request.form
        obj = self.view.virtualTargetObject
        adapter = IType(obj).typeInterface(obj)
        for k in form.keys():
            if k.startswith(prefix):
                fn = k[len(prefix):]
                if fn in ('action', 'type',) or fn.endswith('-empty-marker'):
                    continue
                value = form[k]
                if fn.startswith(conceptPrefix):
                    self.assignConcepts(obj, fn[len(conceptPrefix):], value)
                else:
                    setattr(adapter, fn, value)
        notify(ObjectModifiedEvent(obj))
        return True

    def assignConcepts(self, obj, fieldName, value):
        if value and fieldName == 'search.text_selected':
            concept = util.getObjectForUid(value)
            obj.assignConcept(concept)


