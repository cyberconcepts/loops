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

from loops.browser.action import Action, DialogAction
from loops.browser.concept import ConceptView
from loops.browser.form import CreateConceptForm, EditConceptForm
from loops.browser.form import CreateConcept, EditConcept
from loops.common import adapted
from loops import util


view_macros = ViewPageTemplateFile('view_macros.pt')


class GlossaryView(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['glossary']

    def getActions(self, category='object', page=None):
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
                  page=page))
        return actions


class GlossaryItemView(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['glossaryitem']

    def getActions(self, category='object', page=None):
        actions = []
        if category == 'portlet':
            actions.append(DialogAction(self, title='Edit Glossary Item...',
                  description='Modify glossary item.',
                  viewName='edit_glossaryitem.html',
                  dialogName='editGlossaryItem',
                  page=page))
        return actions


class CreateGlossaryItemForm(CreateConceptForm):

    @Lazy
    def customMacro(self):
        return view_macros.macros['children']


class EditGlossaryItemForm(CreateGlossaryItemForm, EditConceptForm):

    title = _(u'Edit Glossary Item')

    @Lazy
    def macro(self):
        return self.template.macros['edit']

