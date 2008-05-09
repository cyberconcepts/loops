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
Views and actions for states management.

$Id$
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import Action, actions
from cybertools.stateful.interfaces import IStateful
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.expert import query
from loops.search.browser import template as search_template
from loops.util import _


statefulActions = ('loops.classification_quality',
                   'loops.simple_publishing',)


class StateAction(Action):

    url = None
    definition = None

    @Lazy
    def stateful(self):
        return component.getAdapter(self.view.context, IStateful,
                                    name=self.definition)

    @Lazy
    def description(self):
        return (u'State information for %s: %s' %
                (self.definition, self.stateObject.title))

    @Lazy
    def stateObject(self):
        return self.stateful.getStateObject()

    @Lazy
    def icon(self):
        icon = self.stateObject.icon or 'led%s.png' % self.stateObject.color
        return 'cybertools.icons/' + icon


for std in statefulActions:
    actions.register('state.' + std, 'object', StateAction,
            definition = std,
            cssClass='icon-action',
    )


#class StateQuery(ConceptView):
class StateQuery(BaseView):

    template = ViewPageTemplateFile('view_macros.pt')

    @Lazy
    def search_macros(self):
        return search_template.macros

    @Lazy
    def macro(self):
        return self.template.macros['query']

    @Lazy
    def results(self):
        uids = query.State('loops.classification_quality',
                           #['new', 'unclassified', 'classified']).apply()
                           ['new', 'unclassified']).apply()
        return self.viewIterator(query.getObjects(uids, self.loopsRoot))
