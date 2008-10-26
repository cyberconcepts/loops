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
Definition of basic view classes and other browser related stuff for the
loops.expert package.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getParent

from cybertools.browser.form import FormController
from loops.browser.common import BaseView, concept_macros
from loops.browser.concept import ConceptView
from loops.browser.resource import ResourceView, ResourceRelationView
from loops.common import adapted
from loops import util
from loops.util import _


queryTemplate = ViewPageTemplateFile('query.pt')


#class BaseQueryView(ConceptView):
class BaseQueryView(BaseView):

    template = queryTemplate
    childViewFactory = ResourceRelationView
    showCheckboxes = True
    form_action = 'execute_query_action'

    @Lazy
    def macro(self):
        return self.template.macros['query']

    @property
    def infos(self):
        return concept_macros.macros

    @property
    def listings(self):
        return concept_macros.macros

    @Lazy
    def targetPredicate(self):
        return self.conceptManager['querytarget']

    @Lazy
    def defaultPredicate(self):
        return self.conceptManager.getDefaultPredicate()

    @Lazy
    def targets(self):
        return self.context.getChildren([self.targetPredicate])

    def queryInfo(self):
        targetNames = ', '.join(["'%s'" % t.title for t in self.targets])
        return _(u'Selection using: $targets',
                 mapping=dict(targets=targetNames))

    def results(self):
        for t in self.targets:
            for r in t.getResourceRelations([self.defaultPredicate]):
                yield self.childViewFactory(r, self.request, contextIsSecond=True)


class ActionExecutor(FormController):

    def update(self):
        form = self.request.form
        actions = [k for k in form.keys() if k.startswith('action.')]
        if actions:
            uids = form.get('selection', [])
            action = actions[0]
            if action == 'action.delete':
                print '*** delete', uids
                for uid in uids:
                    obj = util.getObjectForUid(uid)
                    parent = getParent(obj)
                    del parent[getName(obj)]
        return True
