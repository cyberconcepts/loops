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
from cybertools.stateful.interfaces import IStateful, IStatesDefinition
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.expert.query import And, Or, State, Type, getObjects
from loops.search.browser import template as search_template
from loops.util import _


statefulActions = ('classification_quality',
                   'simple_publishing',)


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
    def statesDefinitions(self):
        result = {}
        result['resource'] = [component.getUtility(IStatesDefinition, name=n)
                for n in self.globalOptions('organize.stateful.resource', ())]
        result['concept'] = [component.getUtility(IStatesDefinition, name=n)
                for n in self.globalOptions('organize.stateful.concept', ())]
        return result

    @Lazy
    def selectedStates(self):
        result = {}
        for k, v in self.request.form.items():
            if k.startswith('state.') and v:
                result[k] = v
        return result

    @Lazy
    def results(self):
        conceptCriteria = {}
        resourceCriteria = {}
        q = None
        for k, v in self.selectedStates.items():
            k = k[len('state.'):]
            type, statesDef = k.split('.')
            if type == 'concept':
                conceptCriteria[statesDef] = v
            elif type == 'resource':
                resourceCriteria[statesDef] = v
        if conceptCriteria:
            conceptQuery = And(Type('loops:concept:*'),
                               *[State(c, v) for c, v in conceptCriteria.items()])
        if resourceCriteria:
            resourceQuery = And(Type('loops:resource:*'),
                               *[State(c, v) for c, v in resourceCriteria.items()])
            if conceptCriteria:
                q = Or(conceptQuery, resourceQuery)
            else:
                q = resourceQuery
        elif conceptCriteria:
            q = conceptQuery
        if q is not None:
            uids = q.apply()
            return self.viewIterator(getObjects(uids, self.loopsRoot))
        return []