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

from loops.browser.action import Action
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops import util


template = ViewPageTemplateFile('view_macros.pt')


class GlossaryView(ConceptView):

    @Lazy
    def macro(self):
        return template.macros['glossary']

    def getActions(self, category='object', page=None):
        actions = []
        if category == 'portlet':
            actions.append(Action(self, title='Create Glossary Item...',
                  description='Create a new glossary item.',
                  url='create_concept.html',
                  onClick="objectDialog('createGlossaryItem', "
                          "             '%s/create_concept.html?qualifier=concept"
                          "&form.type=.loops/concepts/topic"
                          "&inner_form=inner_concept_form.html"
                          "&dialog=createGlossaryItem'); "
                          "return false;" % page.virtualTargetUrl,
                  innerHtmlId='dialog.createGlossaryItem'))
        return actions


class GlossaryItemView(ConceptView):

    @Lazy
    def macro(self):
        return template.macros['glossaryitem']

    def getActions(self, category='object', page=None):
        actions = []
        if category == 'portlet':
            actions.append(Action(self, title='Edit Glossary Item...',
                  description='Modify glossary item.',
                  url='edit_concept.html',
                  onClick="objectDialog('editGlossaryItem', "
                          "             '%s/edit_concept.html"
                          "?dialog=editGlossaryItem'); "
                          "return false;" % page.virtualTargetUrl,
                  innerHtmlId='dialog.editGlossaryItem'))
        return actions

