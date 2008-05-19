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
View classes for glossary and glossary items.

$Id$
"""


from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile

from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.browser.form import CreateConceptForm, EditConceptForm
from loops.browser.form import CreateConcept, EditConcept
from loops.common import adapted
from loops import util
from loops.util import _


view_macros = ViewPageTemplateFile('view_macros.pt')


class GlossaryView(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['glossary']

    def getActions(self, category='object', page=None, target=None):
        actions = []
        if category == 'portlet':
            actions.append(DialogAction(self, title='Create Glossary Item...',
                  description='Create a new glossary item.',
                  viewName='create_glossaryitem.html',
                  dialogName='createGlossaryItem',
                  #qualifier='concept',
                  typeToken='.loops/concepts/glossaryitem',
                  fixedType=True,
                  innerForm='inner_concept_form.html',
                  page=page, target=target))
        return actions


class GlossaryItemView(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['glossaryitem']

    def getActions(self, category='object', page=None, target=None):
        actions = []
        if category == 'portlet':
            lang = self.request.get('loops.language')
            langParam = lang and {'loops.language': lang} or {}
            actions.append(DialogAction(self, title='Edit Glossary Item...',
                  description='Modify glossary item.',
                  viewName='edit_glossaryitem.html',
                  dialogName='editGlossaryItem',
                  addParams=langParam,
                  page=page, target=target))
        return actions


class EditGlossaryItemForm(EditConceptForm, ConceptView):

    title = _(u'Edit Glossary Item')
    form_action = 'edit_glossaryitem'

    @Lazy
    def macro(self):
        return self.template.macros['edit']

    @Lazy
    def customMacro(self):
        return view_macros.macros['children']

    def children(self):
        return ConceptView.children(self.virtualTarget)

    @Lazy
    def relatedPredicate(self):
        return self.loopsRoot.getConceptManager().get('related')

    @Lazy
    def relatedPredicateUid(self):
        pred = self.relatedPredicate
        return pred and util.getUidForObject(pred) or self.defaultPredicateUid


class CreateGlossaryItemForm(CreateConceptForm, EditGlossaryItemForm):

    title = _(u'Create Glossary Item')
    form_action = 'create_glossaryitem'

    def children(self):
        return []


class EditGlossaryItem(EditConcept):

    childPrefix = 'children.'

    oldChildren = None
    selectedChildren = None

    def updateFields(self):
        obj = self.object
        form = self.request.form
        formState = EditConcept.updateFields(self)
        for k in form.keys():
            if k.startswith(self.prefix):
                fn = k[len(self.prefix):]
                value = form[k]
                if fn.startswith(self.childPrefix) and value:
                    self.collectChildren(fn[len(self.childPrefix):], value)
        if self.oldChildren or self.selectedChildren:
            self.assignChildren(obj)
        return formState

    def collectChildren(self, fieldName, value):
        if self.oldChildren is None:
            self.oldChildren = []
        if self.selectedChildren is None:
            self.selectedChildren = []
        for v in value:
            if fieldName == 'old':
                self.oldChildren.append(v)
            elif fieldName == 'selected' and v not in self.selectedChildren:
                self.selectedChildren.append(v)

    def assignChildren(self, obj):
        for v in self.oldChildren:
            if v not in self.selectedChildren:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                obj.deassignChild(concept, [predicate])
        for v in self.selectedChildren:
            if v != 'none' and v not in self.oldChildren:
                c, p = v.split(':')
                concept = util.getObjectForUid(c)
                predicate = util.getObjectForUid(p)
                exists = obj.getChildRelations([p], concept)
                if not exists:
                    obj.assignChild(concept, predicate)


class CreateGlossaryItem(EditGlossaryItem, CreateConcept):

    def update(self):
        result = CreateConcept.update(self)
        return result

