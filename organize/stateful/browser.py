#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.event import notify
from zope.i18n import translate
from zope.lifecycleevent import ObjectModifiedEvent, Attributes

from cybertools.browser.action import Action, actions
from cybertools.composer.schema.schema import Schema
from cybertools.stateful.interfaces import IStateful, IStatesDefinition
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.browser.form import ObjectForm, EditObject
from loops.expert.query import And, Or, State, Type, getObjects
from loops.expert.browser.search import search_template
from loops.security.common import checkPermission
from loops import util
from loops.util import _


template = ViewPageTemplateFile('view_macros.pt')

statefulActions = ('classification_quality',
                   'simple_publishing',
                   'task_states',
                   'publishable_task',
                   'contact_states',)


def registerStatesPortlet(controller, view, statesDefs,
                          region='portlet_right', priority=98):
    cm = controller.macros
    stfs = [component.getAdapter(view.context, IStateful, name=std) 
                for std in statesDefs]
    cm.register(region, 'states', title=_(u'Workflow'),
                subMacro=template.macros['portlet_states'],
                priority=priority, info=view, stfs=stfs)


class StateAction(Action):

    url = None
    definition = None
    cssClass = 'icon-action'

    @Lazy
    def stateful(self):
        return component.getAdapter(self.view.context, IStateful,
                                    name=self.definition)

    @Lazy
    def description(self):
        lang = self.view.languageInfo.language
        definition = translate(_(self.definition), target_language=lang)
        title = translate(_(self.stateObject.title), target_language=lang)
        return _(u'State information for $definition: $title',
                 mapping=dict(definition=definition, title=title))

    @Lazy
    def stateObject(self):
        return self.stateful.getStateObject()

    @Lazy
    def icon(self):
        return self.stateObject.stateIcon
        #icon = self.stateObject.icon or 'led%s.png' % self.stateObject.color
        #return 'cybertools.icons/' + icon


for std in statefulActions:
    actions.register('state.' + std, 'object', StateAction,
            definition=std,
            cssClass='icon-action',
    )


class ChangeStateBase(object):

    @Lazy
    def stateful(self):
        target = self.view.virtualTargetObject
        if IStateful.providedBy(target):
            return target
        return component.getAdapter(target, IStateful, name=self.definition)

    @Lazy
    def definition(self):
        return self.request.form.get('stdef') or u''

    @Lazy
    def action(self):
        return self.request.form.get('action') or u''

    @Lazy
    def transition(self):
        if self.action:
            return self.stateful.getStatesDefinition().transitions[self.action]

    @Lazy
    def stateObject(self):
        return self.stateful.getStateObject()

    @Lazy
    def schema(self):
        schema = self.transition.schema
        if schema is None:
            return Schema()
        else:
            schema.manager = self
            schema.request = self.request
            return schema


class ChangeStateForm(ChangeStateBase, ObjectForm):

    form_action = 'change_state_action'
    data = {}

    @Lazy
    def macro(self):
        return template.macros['change_state']

    @Lazy
    def title(self):
        return self.virtualTargetObject.title


class ChangeState(ChangeStateBase, EditObject):

    @Lazy
    def stateful(self):
        target = self.target
        if IStateful.providedBy(target):
            return target
        return component.getAdapter(target, IStateful, name=self.definition)

    def update(self):
        formData = self.request.form
        if 'target_uid' in formData:
            self.target = util.getObjectForUid(formData['target_uid'])
        # store data in target object (unless field.nostore)
        self.object = self.target
        formState = self.instance.applyTemplate(data=formData)
        # TODO: check formState
        # track all fields
        trackData = dict(transition=self.action)
        for f in self.fields:
            if f.readonly:
                continue
            name = f.name
            fi = formState.fieldInstances[name]
            rawValue = fi.getRawValue(formData, name, u'')
            trackData[name] = fi.unmarshall(rawValue)
        self.stateful.doTransition(self.action)
        notify(ObjectModifiedEvent(self.target, trackData))
        return True


#class StateQuery(ConceptView):
class StateQuery(BaseView):

    template = template
    form_action = 'execute_search_action'

    @Lazy
    def search_macros(self):
        return search_template.macros

    @Lazy
    def macro(self):
        return self.template.macros['query']

    @Lazy
    def rcStatesDefinitions(self):
        result = {}
        result['resource'] = [component.getUtility(IStatesDefinition, name=n)
                for n in self.globalOptions('organize.stateful.resource', ())]
        result['concept'] = [component.getUtility(IStatesDefinition, name=n)
                for n in self.globalOptions('organize.stateful.concept', ())]
        return result

    @Lazy
    def statesDefinitions(self):
        # TODO: extend to handle concept states as well
        return [component.getUtility(IStatesDefinition, name=n)
                    for n in self.globalOptions('organize.stateful.resource', ())]

    @Lazy
    def selectedStates(self):
        result = {}
        for k, v in self.request.form.items():
            if k.startswith('state.') and v:
                result[k] = v
        return result

    @Lazy
    def showActions(self):
        return checkPermission('loops.ManageSite', self.context)

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


class FilterAllStates(BaseView):

    @Lazy
    def macros(self):
        return template.macros

    @Lazy
    def macro(self):
        return self.macros['filter_allstates']

