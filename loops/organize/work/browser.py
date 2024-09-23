#
#  Copyright (c) 2016 Helmut Merz helmutm@cy55.de
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
"""

from datetime import date
import time
from urllib import urlencode
from zope import component
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName, getParent

from cybertools.ajax import innerHtml
from cybertools.browser.action import actions
from cybertools.meta.interfaces import IOptions
from cybertools.organize.interfaces import IWorkItems
from cybertools.organize.work import workItemTypes
from cybertools.tracking.btree import getTimeStamp
from cybertools.util import format
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.browser.form import ObjectForm, EditObject
from loops.browser.node import NodeView
from loops.common import adapted
from loops.interfaces import IConcept
from loops.organize.interfaces import IPerson
from loops.organize.party import getPersonForUser
from loops.organize.stateful.browser import StateAction
from loops.organize.tracking.browser import BaseTrackView
from loops.organize.tracking.report import TrackDetails
from loops.organize.work.base import WorkItem
from loops.security.common import canAccessObject, canListObject, canWriteObject
from loops.security.common import canAccessRestricted, checkPermission
from loops import util
from loops.util import _


work_macros = ViewPageTemplateFile('work_macros.pt')


# single work items

class WorkItemDetails(TrackDetails):
    """ Render a single work item.
    """

    @Lazy
    def workItemType(self):
        return self.track.getWorkItemType()

    @Lazy
    def description(self):
        return self.track.description

    @Lazy
    def descriptionPlain(self):
        return format.nl2pipe(self.description)

    @Lazy
    def descriptionFormatted(self):
        return format.nl2br(self.description)

    @Lazy
    def deadline(self):
        return self.formatTimeStamp(self.track.deadline, 'date')

    @Lazy
    def deadlineTime(self):
        return self.formatTimeStamp(self.track.deadline, 'time')

    @Lazy
    def deadlineWithTime(self):
        return self.globalOptions('organize.work.deadline_with_time')

    @Lazy
    def start(self):
        result = self.formatTimeStamp(self.track.start, 'time')
        return result != '00:00' and result or ''

    @Lazy
    def end(self):
        result = self.formatTimeStamp(self.track.end, 'time')
        return result != '00:00' and result or ''

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
    def endDay(self):
        endDay = self.formatTimeStamp(self.track.end, 'date')
        return endDay != self.startDay and endDay or ''

    @Lazy
    def created(self):
        return self.formatTimeStamp(self.track.created, 'dateTime')

    def formatTimeDelta(self, value):
        return formatTimeDelta(value)

    @Lazy
    def isLastInRun(self):
        currentWorkItems = list(self.view.workItems.query(runId=self.track.runId))
        return self.track == currentWorkItems[-1]

    @Lazy
    def isToday(self):
        return date.fromtimestamp(self.track.timeStamp) == date.today()

    @Lazy
    def weekDay(self):
        value = date.fromtimestamp(self.track.timeStamp)
        if value is not None:
            return weekDays[value.weekday()].title()

    @Lazy
    def sourceWorkItem(self):
        sourceId = self.track.data.get('source')
        if sourceId:
            return getParent(self.track)[sourceId]

    @Lazy
    def targetWorkItem(self):
        targetId = self.track.data.get('target')
        if targetId:
            return getParent(self.track)[targetId]

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
        #if self.isLastInRun and self.allowedToEditWorkItem:
        if self.allowedToEditWorkItem:
            self.view.registerDojoDateWidget()
            self.view.registerDojoNumberWidget()
            self.view.registerDojoTextarea()
            actions.append(DialogAction(self.view,
                      description=_(u'Edit work item.'),
                      viewName='create_workitem.html',
                      dialogName='',
                      icon='edit.gif',
                      cssClass='icon-action',
                      page=self.view.nodeView,
                      target=self.object,
                      addParams=dict(id=self.track.__name__)))
        return actions

    @Lazy
    def allowedToEditWorkItem(self):
        perm = (self.view.globalOptions('organize.work.permission_edit_workitem')
                 or ['zope.ManageContent'])[0] # 'loops.ManageSite')
        if (self.object is None and 
                checkPermission(perm, self.view.node)):
            return True
        if checkPermission(perm, self.object):
            return True
        return self.user['object'] == getPersonForUser(self.object, self.view.request)


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

    @property
    def macro(self):
        return self.work_macros['workitems_query']

    @Lazy
    def title(self):
        return _(u'Work Items for $title', mapping=dict(title=self.context.title))

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
        tsFrom = parseDate(form.get('wi_from') or
                            self.options.wi_from or self.typeOptions.wi_from)
        tsTo = parseDate(form.get('wi_to') or
                            self.options.wi_to or self.typeOptions.wi_to)
        if tsTo:
            tsTo += 3600 * 24 - 1    # include full end date
        if tsFrom or tsTo:
            result['timeFromTo'] = (tsFrom, tsTo)
        state = (form.get('wi_state') or 
                    self.options.wi_state or self.typeOptions.wi_state)
        if not state:
            result['state'] = ['planned', 'accepted', 'running', 'done', 
                    'done_x', 'finished', 'delegated', 'moved', 'cancelled']
                    #, 'closed']
        elif state != 'all':
            result['state'] = state
        return result

    def query(self, **criteria):
        if self.workItems is None:
            return []
        return [self.detailsFactory(self, wi)
                for wi in self.workItems.query(**criteria)]


class AllWorkItems(BaseWorkItemsView, ConceptView):
    """ Standard view for showing work items independently of task and user.
    """

    columns = set(['Task', 'User', 'Title', 'Day', 'Start', 'End', 'Duration', 'Info'])

    def listWorkItems(self):
        criteria = self.baseCriteria
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


class TaskWorkItems(BaseWorkItemsView, ConceptView):
    """ Standard view for showing work items for a node's target.
    """

    columns = set(['User', 'Title', 'Day', 'Start', 'End', 'Duration', 'Info'])

    @Lazy
    def target(self):
        return self.context

    def listWorkItems(self):
        criteria = self.baseCriteria
        criteria['task'] = util.getUidForObject(self.target)
        # TODO: option: include subtasks
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


class RelatedTaskWorkItems(AllWorkItems):
    """ Show work items for all instances of a concept type assigned to
        the query as query target.
    """

    @Lazy
    def isQueryTarget(self):
        return self.conceptManager['querytarget']

    def listWorkItems(self):
        criteria = self.baseCriteria
        tasks = []
        for parent in self.context.getChildren([self.isQueryTarget]):
            for task in parent.getChildren([self.typePredicate]):
                tasks.append(util.getUidForObject(task))
        criteria['task'] = tasks
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


class PersonWorkItems(BaseWorkItemsView, ConceptView):
    """ A view showing work items for a person or the context object's parents.
    """

    columns = set(['Task', 'Title', 'Day', 'Start', 'End', 'Duration', 'Info'])

    def checkPermissions(self):
        return canAccessRestricted(self.context)

    def getCriteria(self):
        return self.baseCriteria

    def listWorkItems(self):
        criteria = self.getCriteria()
        un = criteria.setdefault('userName', [])
        if IPerson.providedBy(self.adapted):
            un.append(util.getUidForObject(self.context))
        else:
            for target in self.context.getParents([self.defaultPredicate]):
                un.append(util.getUidForObject(target))
        return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


class UserWorkItems(PersonWorkItems):

    @Lazy
    def title(self):
        return self.adapted.title

    def listWorkItems(self):
        criteria = self.getCriteria()
        p = getPersonForUser(self.context, self.request)
        if p is not None:
            criteria['userName'] = util.getUidForObject(p)
            return sorted(self.query(**criteria), key=lambda x: x.track.timeStamp)


# forms and form controllers

class CreateWorkItemForm(ObjectForm, BaseTrackView):

    template = work_macros
    recordManagerName = 'work'
    trackFactory = WorkItem

    def checkPermissions(self):
        return canAccessObject(self.task or self.target)

    def setupView(self):
        self.setupController()
        self.registerDojoComboBox()

    @Lazy
    def macro(self):
        return self.template.macros['create_workitem']

    @Lazy
    def task(self):
        uid = self.track.taskId
        if uid:
            return util.getObjectForUid(uid)

    @Lazy
    def track(self):
        id = self.request.form.get('id')
        if id is not None:
            workItems = self.loopsRoot.getRecordManager()[
                                        self.recordManagerName]
            return workItems.get(id)
        self.task = self.target
        track = self.trackFactory(None, 0, None, {})
        types = self.workItemTypes
        if len(types) == 1:
            track.workItemType = types[0].name
        return track

    @Lazy
    def titleSelection(self):
        result = []
        if self.title:
            return result
        dt = adapted(self.conceptManager.get('organize.work.texts'))
        if dt is None or not dt.data:
            return result
        names = ([getName(self.target)] + 
                 [getName(p.object) 
                    for p in self.target.getAllParents(ignoreTypes=True)])
        for name, text in dt.data.values():
            if not name or name in names:
                result.append(text)
        return result

    @Lazy
    def title(self):
        return self.track.title or u''

    @Lazy
    def description(self):
        return self.track.description or u''

    @Lazy
    def workItemType(self):
        return self.track.getWorkItemType() or self.workItemTypes[0]

    @Lazy
    def workItemTypes(self):
        task = self.task
        if task is None:
            task = self.target
        if IConcept.providedBy(task):
            options = IOptions(adapted(task.conceptType))
            typeNames = options.workitem_types
            if typeNames:
                return [workItemTypes[name] for name in typeNames]
        return workItemTypes

    @Lazy
    def showTypes(self):
        return len(self.workItemTypes) != 1

    @Lazy
    def deadline(self):
        ts = self.track.deadline# or getTimeStamp()
        if ts:
            return time.strftime('%Y-%m-%d', time.localtime(ts))
        return ''

    @Lazy
    def deadlineTime(self):
        ts = self.track.deadline# or getTimeStamp()
        if ts:
            return time.strftime('T%H:%M', time.localtime(ts))
        return ''

    @Lazy
    def deadlineWithTime(self):
        return self.globalOptions('organize.work.deadline_with_time')

    @Lazy
    def defaultTimeStamp(self):
        if self.workItemType.prefillDate:
            return getTimeStamp()
        return None

    @Lazy
    def defaultDate(self):
        return time.strftime('%Y-%m-%dT%H:%M', time.localtime(getTimeStamp()))

    @Lazy
    def date(self):
        ts = self.track.start or self.defaultTimeStamp
        if ts:
            return time.strftime('%Y-%m-%d', time.localtime(ts))
        return ''

    @Lazy
    def endDate(self):
        ts = self.track.end or self.defaultTimeStamp
        if ts:
            return time.strftime('%Y-%m-%d', time.localtime(ts))
        return ''

    @Lazy
    def startTime(self):
        ts = self.track.start or self.defaultTimeStamp
        if ts:
            return time.strftime('T%H:%M', time.localtime(ts))
        return ''

    @Lazy
    def endTime(self):
        if self.state == 'running':
            ts = self.defaultTimeStamp
        else:
            ts = self.track.end or self.defaultTimeStamp
        if ts:
            return time.strftime('T%H:%M', time.localtime(ts))
        return ''

    @Lazy
    def state(self):
        return self.track.state

    @Lazy
    def actions(self):
        defaults = self.globalOptions('organize.work.default_actions') or []
        result = [dict(name=t.name, title=t.title, selected=t.name in defaults)
                    for t in self.track.getAvailableTransitions()
                    if t.name in self.workItemType.actions and
                       t.name not in self.hiddenActions]
                    #and (t.name != 'delegate' or
                    #    checkPermission('loops.ManageSite', self.context))]
        return result

    @Lazy
    def hiddenActions(self):
        task = self.task
        if task is None:
            task = self.target
        if not IConcept.providedBy(task):
            return []
        options = IOptions(adapted(task.conceptType))
        return options.hidden_workitem_actions or []

    def getTypesParamsForFilteringSelect(self, types=['person']):
        result = []
        for t in types:
            result.append('searchType=loops:concept:%s' % t)
        if result:
            return '?' + '&'.join(result)
        return ''

    @Lazy
    def x_candidates(self):
        ptype = self.conceptManager['person']
        persons = ptype.getChildren([self.typePredicate])
        return [dict(name=util.getUidForObject(p), title=p.title)
                    for p in persons]

    @Lazy
    def taskTypes(self):
        return (self.globalOptions('organize.work.task_types') or
                ['task', 'event', 'agendaitem'])

    @Lazy
    def followUpTask(self):
        pred = self.conceptManager.get('follows')
        if pred is not None and self.task is not None:
            for t in self.task.getChildren([pred]):
                return t

    @Lazy
    def x_tasks(self):
        tasks = []
        tnames = self.taskTypes
        ttypes = [self.conceptManager.get(tname) for tname in tnames]
        for ttype in ttypes:
            if ttype is not None:
                tasks.extend(ttype.getChildren([self.typePredicate]))
        return [dict(name=util.getUidForObject(t), title=t.title)
                    for t in tasks]

    @Lazy
    def priorities(self):
        if 'priority' in self.workItemType.fields:
            prio = self.conceptManager.get('organize.work.priorities')
            if prio: 
                return adapted(prio).dataAsRecords()
        return []

    @Lazy
    def activities(self):
        if 'activity' in self.workItemType.fields:
            act = self.conceptManager.get('organize.work.activities')
            if act: 
                return adapted(act).dataAsRecords()
        return []

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

    def onChangeAction(self):
        js = [self.actionJs['setDefault'], 
              self.actionJs['showIf'], 
              self.actionJs['setIfSD']]
        if self.state in ('done',):
            js.append(self.actionJs['setIfWF'])
        return ';\n'.join(js)

    actionJs = dict(setDefault="defValue = this.form.default_date.value",
                    showIf="""
showIfIn(this, [['move', 'target_task'],
                ['delegate', 'target_party']])""",
                    setIfSD="""
setIfN(this, ['start', 'delegate'], [
                        ['start_date', defValue],
                        ['start_time', defValue],
                        ['end_time', null],
                        ['duration', ''],
                        ['effort', '']])""",
                    setIfWF="""
setIfN(this, ['work', 'finish'], [
                        ['start_date', defValue],
                        ['start_time', null],
                        ['end_time', null],
                        ['duration', ''],
                        ['effort', '']])""",
)


class CreateWorkItem(EditObject, BaseTrackView):

    def checkPermissions(self):
        return canAccessObject(self.task or self.target)

    @Lazy
    def task(self):
        if self.track is None:
            return None
        uid = self.track.taskId
        if uid:
            return util.getObjectForUid(uid)

    @Lazy
    def track(self):
        id = self.request.form.get('id')
        if id is not None:
            workItems = self.loopsRoot.getRecordManager()['work']
            return workItems.get(id)

    @Lazy
    def object(self):
        return self.target
        #return self.view.virtualTargetObject

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
        for k in ('workItemType', 'title', 'description', 'comment'):
            setValue(k)
        if action == 'delegate':
            setValue('party')
        if action == 'move':
            setValue('task')
        #result['deadline'] = parseDate(form.get('deadline'))
        deadline = form.get('deadline')
        if deadline:
            deadlineTime = (form.get('deadline_time', '').
                                strip().replace('T', '') or '00:00:00')
            result['deadline'] = parseDateTime('T'.join((deadline, deadlineTime)))
        else:
            result['deadline'] = None
        result['priority'] = form.get('priority')
        result['activity'] = form.get('activity')
        startDate = form.get('start_date', '').strip()
        endDate = form.get('end_date', '').strip() or startDate
        startTime = form.get('start_time', '').strip().replace('T', '') or '00:00:00'
        endTime = form.get('end_time', '').strip().replace('T', '') or '00:00:00'
        if startDate:
            result['start'] = parseDateTime('T'.join((startDate, startTime)))
            result['end'] = parseDateTime('T'.join((endDate, endTime)))
        result['duration'] = parseTime(form.get('duration'))
        result['effort'] = parseTime(form.get('effort'))
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
        #notify(ObjectModifiedEvent(obj))
        url = self.view.virtualTargetUrl
        #url = self.request.URL
        # append sortinfo parameters:
        #urlParams = {}
        #for k, v in self.view.sortInfo.items():
        #    urlParams['sortinfo_' + k] = v['fparam']
        #if urlParams:
        #    url = '%s?%s' % (url, urlencode(urlParams))
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

specialDays = ['yesterday', 'today', 'tomorrow']
weekDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

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
    if isinstance(s, (list, tuple)):
        s = s[0]
    if s[0] in ('-', '+') or s.isdigit():
        delta = int(s) * 3600 * 24
        return int(time.mktime(date.today().timetuple())) + delta
    elif s in specialDays:
        delta = (specialDays.index(s) - 1) * 3600 * 24
        return int(time.mktime(date.today().timetuple())) + delta
    elif s in weekDays:
        wd = weekDays.index(s)
        today = date.today()
        todayWd = today.weekday
        delta = (wd + 8 - todayWd) % 8
        return int(time.mktime(today.timetuple())) + delta
    return int(time.mktime(time.strptime(s, '%Y-%m-%d')))

def formatTimeDelta(value):
    if not value:
        return u''
    h, m = divmod(int(value) / 60, 60)
    if h > 24:
        #d, h = divmod(h / 24, 24)
        #return u'%id %02i:%02i' % (d, h, m) 
        return str(int(round(h / 24.0)))
    return u'%02i:%02i' % (h, m)


class FixCheckupWorkItems(object):

    def __call__(self):
        context = removeSecurityProxy(self.context)
        rm = context['records']['work']
        count = 0
        workItems = list(rm.values())
        for wi in workItems:
            if wi.state in ('done',):
                if wi.workItemType != 'checkup':
                    print '*** done, but not checkup', wi.__name__
                    continue
                wi.state = 'running'
                wi.reindex('state')
                if wi.end == wi.start:
                    del wi.data['end']
                count += 1
        msg = '*** checked: %i, updated: %i.' % (len(workItems), count)
        print msg
        return msg

