#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
View class(es) for work items.

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
from loops.browser.concept import ConceptView
from loops.browser.form import ObjectForm, EditObject
from loops.browser.node import NodeView
from loops.organize.party import getPersonForUser
from loops.organize.tracking.browser import BaseTrackView
from loops.organize.tracking.report import TrackDetails
from loops import util
from loops.util import _


work_macros = ViewPageTemplateFile('work_macros.pt')


# work item collections

class BaseWorkItemsView(object):

    columns = set(['Task', 'User', 'Title', 'Start', 'End', 'Duration'])

    lastMonth = lastDay = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def work_macros(self):
        return work_macros.macros

    @Lazy
    def workItems(self):
        ts = self.loopsRoot.getRecordManager().get('work')
        if ts is not None:
            return IWorkItems(ts)


class WorkItemsView(BaseWorkItemsView, NodeView):
    """ Standard view for showing work items for a node's target.
    """

    columns = set(['User', 'Title', 'Day', 'Start', 'End', 'Duration'])

    @Lazy
    def allWorkItems(self):
        result = []
        target = self.virtualTargetObject
        workItems = self.workItems
        if None in (workItems, target):
            return result
        for wi in workItems.query(task=util.getUidForObject(target)):
            result.append(WorkItemDetails(self, wi))
        return sorted(result, key=lambda x: x.track.timeStamp)


class UserWorkItems(BaseWorkItemsView, ConceptView):
    """ A query view showing work items for a person, the query's parent.
    """

    columns = set(['Task', 'Title', 'Day', 'Start', 'End', 'Duration'])

    @property
    def macro(self):
        return self.work_macros['userworkitems']

    @Lazy
    def allWorkItems(self):
        workItems = self.workItems
        if self.workItems is None:
            return []
        result = []
        for target in self.context.getParents([self.defaultPredicate]):
            for wi in workItems.query(userName=util.getUidForObject(target)):
                result.append(WorkItemDetails(self, wi))
        return sorted(result, key=lambda x: x.track.timeStamp)


# single work items

class WorkItemDetails(TrackDetails):
    """ Render a single work item.
    """

    @Lazy
    def description(self):
        return self.track.description

    @Lazy
    def start(self):
        return self.formatTimeStamp(self.track.start, 'time')

    @Lazy
    def end(self):
        return self.formatTimeStamp(self.track.end, 'time')

    @Lazy
    def duration(self):
        return self.formatTimeDelta(self.track.duration)

    @Lazy
    def effort(self):
        return self.formatTimeDelta(self.track.effort)

    def formatTimeDelta(self, value):
        if not value:
            return ''
        h, m = divmod(int(value) / 60, 60)
        return '%02i:%02i' % (h, m)


class WorkItemView(BaseTrackView):
    """ Show a single work item in the management view.
    """


# forms and form controllers

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

    def processForm(self):
        form = self.request.form
        action = form.get('workitem.action')
        if not action:
            return None, {}
        result = dict()
        def setValue(k):
            v = form.get(k)
            if v:
                result[k] = v
        for k in ('title', 'description', 'comment'):
            setValue(k)
        startDate = form.get('start_date')
        startTime = form.get('start_time')
        endTime = form.get('end_time')
        if startDate and startTime:
            result['start'] = parseDateTime(startDate + startTime)
        if startDate and endTime:
            result['end'] = parseDateTime(startDate + endTime)
        duration = form.get('duration')
        if duration:
            result['duration'] = parseTime(duration)
        effort = form.get('effort')
        if effort:
            result['effort'] = parseTime(effort)
        return action, result

    def update(self):
        rm = self.view.loopsRoot.getRecordManager()
        workItems = IWorkItems(rm.get('work'))
        action, data = self.processForm()
        if not action:
            return True
        wi = workItems.add(util.getUidForObject(self.object), self.personId)
        wi.doAction(action, self.personId, **data)
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


# auxiliary functions

def parseTime(s):
    if ':' in s:
        h, m = [int(v) for v in s.split(':')]
    else:
        h, m = int(s), 0
    return h * 3600 + m * 60

def parseDateTime(s):
    return int(time.mktime(time.strptime(s, '%Y-%m-%dT%H:%M:%S')))
