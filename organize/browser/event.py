#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff for tasks.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops.util import _


organize_macros = ViewPageTemplateFile('view_macros.pt')


class Events(ConceptView):

    @Lazy
    def macro(self):
        return organize_macros.macros['events']

    def getActions(self, category='object', page=None):
        actions = []
        if category == 'portlet':
            actions.append(DialogAction(self, title=_(u'Create Event...'),
                  description=_(u'Create a new event.'),
                  viewName='create_concept.html',
                  dialogName='createEvent',
                  typeToken='.loops/concepts/event',
                  fixedType=True,
                  innerForm='inner_concept_form.html',
                  page=page))
            self.registerDojoDateWidget()
        return actions

    def events(self):
        cm = self.loopsRoot.getConceptManager()
        tEvent = cm['event']
        hasType = cm.getTypePredicate()
        sort = lambda x: adapted(x.second).start
        for r in tEvent.getChildRelations([hasType], sort=sort):
            yield self.childViewFactory(r, self.request, contextIsSecond=True)

