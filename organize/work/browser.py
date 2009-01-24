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

from cybertools.ajax import innerHtml
from cybertools.browser.action import actions
from cybertools.organize.interfaces import IWorkItems
from cybertools.tracking.btree import getTimeStamp
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.browser.form import ObjectForm, EditObject
from loops.browser.node import NodeView
from loops.organize.party import getPersonForUser
from loops.organize.stateful.browser import StateAction
from loops.organize.tracking.browser import BaseTrackView
from loops.organize.tracking.report import TrackDetails
from loops.organize.work.base import WorkItem
from loops import util
from loops.util import _


work_macros = ViewPageTemplateFile('work_macros.pt')


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

    @Lazy
    def startDay(self):
        return self.formatTimeStamp(self.track.timeStamp, 'date')

    @Lazy
    def created(self):
        return self.formatTimeStamp(self.track.created, 'dateTime')

    def formatTimeDelta(self, value):
        return formatTimeDelta(value)

    @Lazy
    def isLastInRun(self):
        currentWorkItems = list(self.view.workItems.query(runId=self.track.runId))
        return self.track == currentWorkItems[-1]

    def actions(self):
        info = DialogAction(self.view,
                      description=_(u'Information about this work item.'),
                      viewName='workitem_info.html',
                      dialogName='',
                      icon='cybertools.icons/info.png',
                      cssClass='icon-action',
                      page=self.view.nodeView,
                      target=self.object,
                      addParams=dict(id=self.track.__name__))
        actions = [info, WorkItemStateAction(self)]
        if self.isLastInRun:
            self.view.registerDojoDateWidget()
            self.view.registerDojoNumberWidget()
            self.view.registerDojoTextarea()
            actions.append(DialogAction(self.view,
                      description=_(u'Create a work item.'),
                      viewName='create_workitem.html',
                      dialogName='',
                      icon='edit.gif',
                      cssClass='icon-action',
                      page=self.view.nodeView,
                      target=self.object,
                      addParams=dict(id=self.track.__name__)))
        return actions


class WorkItemInfo(NodeView):
    """ Provides info box.
    """

    __call__ = innerHtml

    @property
    def macro(self):
        return work_macros.macros['workitem_info']

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'workitem_info')

    @Lazy
    def track(self):
        id = self.request.form.get('id')
        if id is not None:
            workItems = self.loopsRoot.getRecordManager()['work']
            track = workItems.get(id)
            return WorkItemDetails(self, track)


class WorkItemView(BaseTrackView):
    """ Show a single work item in the management view.
    """


# work item collections

class BaseWorkItemsView(object):

    allColumns = ['Day', 'Start', 'End', 'Duration', 'Task', 'User', 'Title', 'Info']
    columns = set(allColumns)
    detailsFactory = WorkItemDetails

    lastMonth = lastDay = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def work_macros(self):
        return work_macros.macros

    @Lazy
    def workItems(self):
        rm = self.loopsRoot.getRecordManager()
        if rm is not None:
            ts = rm.get('work')
            if ts is not None:
                return IWorkItems(ts)

    @Lazy
    def baseCriteria(self):
        result = {}
        form = self.request.form
        start = parseDate(form.get('wi_start'))
        end = parseDate(form.get('wi_end'))
        if end:
            end += 3600 * 24    # include full end date
        if start or end:
            result['timeFromTo'] = (start, end)
        state = form.get('wi_state')
        if state is not None:
            result['state'] = state
        return result

    def query(self, **criteria):
        if self.workItems is None:
            return []
        return [self.detailsFactory(self, wi)
                for wi in self.workItems.query(**criteria)]


class WorkItemsView(BaseWorkItemsView, NodeView):
    """ Standard view for showing work items for a node's target.
    """

    columns = set(['User', 'Title', 'Day', 'Start', 'End', 'Duration', 'Info'])

    @Lazy
    def listWorkItems(self):
        target = self.virtualTargetObject
        criteria = self.baseCriteria
        criteria['task'] = util.getUidForObject(target)
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


class PersonWorkItems(BaseWorkItemsView, ConceptView):
    """ A query view showing work items for a person, the query's parent.
    """

    columns = set(['Task', 'Title', 'Day', 'Start', 'End', 'Duration', 'Info'])

    @property
    def macro(self):
        return self.work_macros['userworkitems']

    def getCriteria(self):
        crit = self.baseCriteria
        tft = crit.get('timeFromTo') or (None, None)
        if not tft[0]:
            tft = (getTimeStamp() - (3 * 24 * 3600), tft[1])
            crit['timeFromTo'] = tft
        if not crit.get('state'):
            crit['state'] = ['planned', 'accepted', 'running', 'done', 'done_x',
                             'finished', 'delegated']
        return crit

    @Lazy
    def listWorkItems(self):
        criteria = self.getCriteria()
        for target in self.context.getParents([self.defaultPredicate]):
            un = criteria.setdefault('userName', [])
            un.append(util.getUidForObject(target))
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


# forms and form controllers

class CreateWorkItemForm(ObjectForm, BaseTrackView):

    template = work_macros

    @Lazy
    def macro(self):
        return self.template.macros['create_workitem']

    @Lazy
    def track(self):
        id = self.request.form.get('id')
        if id is not None:
            workItems = self.loopsRoot.getRecordManager()['work']
            return workItems.get(id)
        return WorkItem(None, 0, None, {})

    @Lazy
    def title(self):
        return self.track.title or u''

    @Lazy
    def description(self):
        return self.track.description or u''

    @Lazy
    def date(self):
        ts = self.track.start or getTimeStamp()
        return time.strftime('%Y-%m-%d', time.localtime(ts))

    @Lazy
    def startTime(self):
        ts = self.track.start or getTimeStamp()
        #return time.strftime('%Y-%m-%dT%H:%M', time.localtime(ts))
        return time.strftime('T%H:%M', time.localtime(ts))

    @Lazy
    def endTime(self):
        if self.state == 'running':
            ts = getTimeStamp()
        else:
            ts = self.track.end or getTimeStamp()
        #return time.strftime('%Y-%m-%dT%H:%M', time.localtime(ts))
        return time.strftime('T%H:%M', time.localtime(ts))

    @Lazy
    def state(self):
        return self.track.state

    @Lazy
    def actions(self):
        return [dict(name=t.name, title=t.title)
                    for t in self.track.getAvailableTransitions()]

    @Lazy
    def duration(self):
        if self.state == 'running':
            return u''
        return formatTimeDelta(self.track.duration)

    @Lazy
    def effort(self):
        if self.state == 'running':
            return u''
        return formatTimeDelta(self.track.effort)

    @Lazy
    def comment(self):
        return self.track.comment or u''


class CreateWorkItem(EditObject, BaseTrackView):

    @Lazy
    def track(self):
        id = self.request.form.get('id')
        if id is not None:
            workItems = self.loopsRoot.getRecordManager()['work']
            return workItems.get(id)

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
        startDate = form.get('start_date', '').strip()
        startTime = form.get('start_time', '').strip().replace('T', '')
        endTime = form.get('end_time', '').strip().replace('T', '')
        #print '***', startDate, startTime, endTime
        if startDate and startTime:
            result['start'] = parseDateTime('T'.join((startDate, startTime)))
        if startDate and endTime:
            result['end'] = parseDateTime('T'.join((startDate, endTime)))
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
        if self.track is not None:
            wi = self.track
        else:
            wi = workItems.add(util.getUidForObject(self.object), self.personId)
        wi.doAction(action, self.personId, **data)
        url = self.view.virtualTargetUrl
        #url = self.request.URL
        self.request.response.redirect(url)
        return False


# actions

actions.register('createWorkitem', 'portlet', DialogAction,
        title=_(u'Create Work Item...'),
        description=_(u'Create a work item for this object.'),
        viewName='create_workitem.html',
        dialogName='createWorkitem',
        prerequisites=['registerDojoDateWidget', 'registerDojoNumberWidget',
                       'registerDojoTextarea'],
)


class WorkItemStateAction(StateAction):

    cssClass = 'icon-action'

    @Lazy
    def stateful(self):
        return self.view.track

    @Lazy
    def description(self):
        return _(self.stateObject.title)


# auxiliary functions

def parseTime(s):
    if not s:
        return None
    if ':' in s:
        h, m = [int(v) for v in s.split(':')]
    else:
        h, m = int(s), 0
    return h * 3600 + m * 60

def parseDateTime(s):
    if not s:
        return None
    return int(time.mktime(time.strptime(s, '%Y-%m-%dT%H:%M:%S')))

def parseDate(s):
    if not s:
        return None
    return int(time.mktime(time.strptime(s, '%Y-%m-%d')))

def formatTimeDelta(value):
    if not value:
        return u''
    h, m = divmod(int(value) / 60, 60)
    return u'%02i:%02i' % (h, m)

