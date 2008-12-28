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
View class(es) for change tracks.

$Id$
"""

import time
from zope import component
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.browser.action import actions
from cybertools.organize.interfaces import IWorkItems
from loops.browser.action import DialogAction
from loops.browser.form import ObjectForm, EditObject
from loops.organize.party import getPersonForUser
from loops.organize.tracking.browser import BaseTrackView
from loops import util
from loops.util import _


work_macros = ViewPageTemplateFile('work_macros.pt')


class WorkItemView(BaseTrackView):

    pass


class CreateWorkItemForm(ObjectForm, BaseTrackView):

    template = work_macros

    @Lazy
    def macro(self):
        return self.template.macros['create_workitem']

    @Lazy
    def defaultDate(self):
        return time.strftime('%Y-%m-%d')

    @Lazy
    def defaultTime(self):
        return time.strftime('%Y-%m-%dT%H:%M')


class CreateWorkItem(EditObject, BaseTrackView):

    @Lazy
    def personId(self):
        p = getPersonForUser(self.context, self.request)
        if p is not None:
            return util.getUidForObject(p)
        return self.request.principal.id

    @Lazy
    def object(self):
        return self.view.virtualTargetObject

    @Lazy
    def data(self):
        result = {}
        form = self.request.form
        #print '***', form
        return result

    def update(self):
        rm = self.view.loopsRoot.getRecordManager()
        workItems = IWorkItems(rm.get('work'))
        wi = workItems.add(util.getUidForObject(self.object), self.personId)
        wi.doAction('finish', **self.data)
        url = self.view.virtualTargetUrl + '?version=this'
        self.request.response.redirect(url)
        return False


# actions

actions.register('createWorkitem', 'portlet', DialogAction,
        title=_(u'Create Work Item...'),
        description=_(u'Create a work item for this object.'),
        viewName='create_workitem.html',
        dialogName='createWorkitem',
        prerequisites=['registerDojoDateWidget', 'registerDojoNumberWidget'],
)
