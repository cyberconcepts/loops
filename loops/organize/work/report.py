#
#  Copyright (c) 2018 Helmut Merz helmutm@cy55.de
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
Work report definitions.
"""

from datetime import date, timedelta
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapter, getAdapter
from zope.i18n.locales import locales

from cybertools.composer.report.base import Report
from cybertools.composer.report.base import LeafQueryCriteria, CompoundQueryCriteria
from cybertools.composer.report.field import CalculatedField
from cybertools.composer.report.result import ResultSet, Row as BaseRow
from cybertools.meta.interfaces import IOptions
from cybertools.organize.interfaces import IWorkItems
from cybertools.stateful.interfaces import IStateful
from cybertools.util.date import timeStamp2Date, timeStamp2ISO
from cybertools.util.jeep import Jeep
from loops.common import adapted, baseObject
from loops.expert.browser.export import ResultsConceptCSVExport
from loops.expert.browser.report import ReportConceptView
from loops.expert.field import Field, TargetField, DateField, StateField, \
                            StringField, TextField, HtmlTextField, \
                            UrlField, VocabularyField
from loops.expert.field import SubReport, SubReportField
from loops.expert.field import TrackDateField, TrackTimeField, TrackDateTimeField
from loops.expert.field import WorkItemStateField
from loops.expert.report import ReportInstance
from loops.table import DataTableSourceBinder, DataTableSourceListByValue
from loops import util


# reporting views

class WorkStatementView(ReportConceptView):

    reportName = 'work_statement'


class WorkPlanView(ReportConceptView):

    reportName = 'work_plan'


class WorkStatementCSVExport(ResultsConceptCSVExport):

    reportName = 'work_statement'


# fields

class DurationField(Field):

    factor = 1
    cssClass = 'right'

    def getValue(self, row):
        value = self.getRawValue(row) or 0
        value = float(value)
        if value and 'totals' in self.executionSteps:
            data = row.parent.totals.data
            data[self.name] = data.get(self.name, 0) + value
        if value:
            value = value * self.factor / 3600.0
        return value

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if not value:
            return u''
        return u'%02i:%02i' % divmod(value * 60, 60)

    def getExportValue(self, row, format, lang):
        value = self.getValue(row)
        if format == 'csv':
            return '%i' % round(value * 60)
            locale = locales.getLocale(lang)
            fmt = locale.numbers.getFormatter('decimal')
            return fmt.format(value, pattern=u'0.0000;-0.0000')            
        return value


class PartyStateField(StateField):

    def getValue(self, row):
        context = row.context
        if context is None:
            return None
        party = util.getObjectForUid(context.party)
        ptype = adapted(party.conceptType)
        stdefs = IOptions(ptype)('organize.stateful') or []
        if self.statesDefinition in stdefs:
            stf = getAdapter(party, IStateful, 
                             name=self.statesDefinition)
            return stf.state

    def getContext(self, row):
        if row.context is None:
            return None
        party = util.getObjectForUid(row.context.party)
        ptype = adapted(party.conceptType)
        stdefs = IOptions(ptype)('organize.stateful') or []
        if self.statesDefinition in stdefs:
            return party
        return None


class PartyQueryField(TargetField):

    def getVocabularyItems(self, row=None, context=None, request=None):
        concepts = context.getLoopsRoot().getConceptManager()
        sourceQuery = concepts.get('participants')
        if sourceQuery is None:
            return []
        persons = sourceQuery.getChildren()
        return [dict(token=util.getUidForObject(p), title=p.title) 
                for p in persons]


class ActivityField(VocabularyField):

    tableName = 'organize.work.activities'
    vocabulary = DataTableSourceBinder(tableName, 
                    sourceList=DataTableSourceListByValue)

    def getDisplayValue(self, row):
        if row.context is None:
            return u'-'
        value = row.context.data.get('activity', '')#[:3]
        if not value:
            return u''
        dt = row.parent.context.view.conceptManager.get(self.tableName)
        if dt is None:
            return u''
        for row in adapted(dt).data.values():
            if row[0] == value:
                value = row[3]
                break
        return value


def daysAgoByOption(context):
    days = 7
    opt = context.view.typeOptions('workitem_dayfrom_default')
    if opt:
        if opt is True or not opt[0].isdigit():
            return None
        else:
            days = int(opt[0])
    return (date.today() - timedelta(days)).isoformat()


# common fields

tasks = Field('tasks', u'Tasks',
                description=u'The tasks from which sub-tasks and '
                        u'work items should be selected.',
                executionSteps=['query'])

# work report fields

deadline = TrackDateField('deadline', u'Deadline',
                description=u'The day the work has to be finished.',
                cssClass='center',
                executionSteps=['sort', 'output'])
dayFrom = TrackDateField('dayFrom', u'Start Day',
                description=u'The first day from which to select work.',
                fieldType='date',
                default=daysAgoByOption,
                operator=u'ge',
                executionSteps=['query'])
dayTo = TrackDateField('dayTo', u'End Day',
                description=u'The last day until which to select work.',
                fieldType='date',
                operator=u'le',
                executionSteps=['query'])
day = TrackDateField('day', u'Day',
                description=u'The day the work was done.',
                cssClass='center',
                executionSteps=['sort', 'output'])
dayStart = TrackDateField('dayStart', u'Start Day',
                description=u'The day the unit of work was started.',
                cssClass='center',
                executionSteps=['sort', 'output'])
dayEnd = TrackDateField('dayEnd', u'End Day',
                description=u'The day the unit of work was finished.',
                cssClass='center',
                executionSteps=['sort', 'output'])
timeStart = TrackTimeField('start', u'Start',
                description=u'The time the unit of work was started.',
                executionSteps=['sort', 'output'])
timeEnd = TrackTimeField('end', u'End',
                description=u'The time the unit of work was finished.',
                executionSteps=['output'])
task = TargetField('taskId', u'Task',
                description=u'The task to which work items belong.',
                executionSteps=['sort', 'output'])
party = PartyQueryField('userName', u'Party',
                description=u'The party (usually a person) who did the work.',
                fieldType='selection',
                executionSteps=['sort', 'output', 'query'])
#partyQuery = TargetField('userName', u'Party',
#                description=u'The party (usually a person) who did the work.',
#                fieldType='selection',
#                executionSteps=['query'])
workTitle = StringField('title', u'Title',
                description=u'The short description of the work.',
                executionSteps=['sort', 'output'])
workDescription = StringField('description', u'Description',
                description=u'The long description of the work.',
                executionSteps=['output'])
duration = DurationField('duration', u'Duration',
                description=u'The duration of the work.',
                executionSteps=['output'])
effort = DurationField('effort', u'Effort',
                description=u'The effort of the work.',
                executionSteps=['output', 'totals'])
state = WorkItemStateField('state', u'State',
                description=u'The state of the work.',
                cssClass='center',
                statesDefinition='workItemStates',
                executionSteps=['query', 'output'])
partyState = PartyStateField('partyState', u'Party State',
                description=u'State of the party, mainly for selection.',
                cssClass='center',
                statesDefinition='contact_states',
                executionSteps=['query', 'output'])
activity = ActivityField('activity', u'LA',
                description=u'The activity assigned to the work item.',
                fieldType='selection',
                executionSteps=['query', 'sort', 'output'])
# process


# basic definitions and work report instance

class WorkRow(BaseRow):

    def getRawValue(self, attr):
        if attr in self.attributeHandlers:
            return self.attributeHandlers[attr](self, attr)
        track = self.context
        if attr in track.metadata_attributes:
            return getattr(track, attr)
        return track.data.get(attr, u'')

    def getDay(self, attr):
        return self.context.timeStamp

    def getStart(self, attr):
        return self.context.start

    def getEnd(self, attr):
        return self.context.end

    def getDuration(self, attr):
        value = self.context.data.get('duration')
        if value is None:
            value = self.getRawValue('end') - self.getRawValue('start')
        return value

    def getEffort(self, attr):
        value = self.context.data.get('effort')
        if value is None:
            value = self.getDuration(attr)
        return value

    attributeHandlers = dict(day=getDay, 
                             dayStart=getStart, dayEnd=getEnd,
                             dayFrom=getDay, dayTo=getDay,
                             duration=getDuration, effort=getEffort)


class WorkReportInstance(ReportInstance):

    type = "work_statement"
    label = u'Work Statement'

    rowFactory = WorkRow

    fields = Jeep((dayFrom, dayTo, tasks,
                   day, timeStart, timeEnd, task, party, workTitle, 
                   #description,
                   activity,
                   #duration, 
                   effort, state))

    userSettings = (dayFrom, dayTo, party, activity)
    defaultOutputFields = fields
    defaultSortCriteria = (day, timeStart,)
    defaultStates = ('done', 'done_x', 'finished')
    taskTypeNames = ('task', 'event', 'project')

    def getOptions(self, option):
        return self.view.options(option)

    @Lazy
    def states(self):
        return self.getOptions('report_select_state') or self.defaultStates

    def getFieldQueryCriteria(self, field, data):
        if field.name in data:
            return LeafQueryCriteria(
                field.name, field.operator, data[field.name], field)
        else:
            default = field.default
            if default is not None:
                if callable(default):
                    default = default(self)
                if default:
                    return LeafQueryCriteria(
                        field.name, field.operator, default, field)

    @property
    def queryCriteria(self):
        form = self.view.request.form
        crit = self.context.queryCriteria or []
        if not crit and 'tasks' not in form:
            f = self.fields['tasks']
            tasks = [self.view.context]
            tasks = [util.getUidForObject(task) for task in tasks]
            crit = [LeafQueryCriteria(f.name, f.operator, tasks, f)]
        for f in self.getAllQueryFields():
            fc = self.getFieldQueryCriteria(f, form)
            if fc is not None:
                crit.append(fc)
        return CompoundQueryCriteria(crit)

    def selectObjects(self, parts):
        result = []
        for t in self.getTasks(parts):
            result.extend(self.selectWorkItems(t, parts))
        # remove parts already used for selection from parts list:
        parts.pop('userName', None)
        return result

    def getTasks(self, parts):
        taskIds = parts.pop('tasks').comparisonValue
        if not isinstance(taskIds, (list, tuple)):
            taskIds = [taskIds]
        tasks = [util.getObjectForUid(t) for t in taskIds]
        for t in list(tasks):
            tasks.extend(self.getAllSubtasks(t))
        return tasks

    def getAllSubtasks(self, concept, checked=None):
        result = []
        if checked is None:
            #checked = set()
            checked = set([concept])
        for c in concept.getChildren([self.view.defaultPredicate]):
            if c.conceptType in self.taskTypes and c not in checked:
                result.append(c)
            if c not in checked:
                checked.add(c)
                result.extend(self.getAllSubtasks(c, checked))
        return result

    def selectWorkItems(self, task, parts):
        kw = dict(task=util.getUidForObject(baseObject(task)), 
                  state=self.states)
        userNameCrit = parts.get('userName')
        if userNameCrit and userNameCrit.comparisonValue:
            kw['userName'] = userNameCrit.comparisonValue
        wi = self.workItems
        return wi.query(**kw)

    @Lazy
    def taskTypes(self):
        return [c for c in [self.conceptManager.get(name)
                                for name in self.taskTypeNames]
                  if c is not None]

    @Lazy
    def workItems(self):
        return IWorkItems(self.recordManager['work'])


class WorkPlanReportInstance(WorkReportInstance):

    type = "work_plan"
    label = u'Work Plan'

    defaultStates = ('planned', 'accepted', 'done')


class PersonWorkReportInstance(WorkReportInstance):

    type = "person_work_statement"
    label = u'Person Work Statement'

    @property
    def queryCriteria(self):
        crit = self.context.queryCriteria or []
        for f in self.getAllQueryFields():
            fc = self.getFieldQueryCriteria(f, self.view.request.form)
            if fc is not None:
                crit.append(fc)
        return CompoundQueryCriteria(crit)

    def selectObjects(self, parts):
        workItems = self.recordManager['work']
        person = self.view.context
        uid = util.getUidForObject(person)
        return workItems.query(userName=uid, state=self.states)


# meeting minutes

class MeetingMinutesWorkRow(WorkRow):

    @Lazy
    def isActive(self):
        return self.context.state not in (
            'finished', 'finished_x', 'closed', 'cancelled', 'moved')


class MeetingMinutesWork(WorkReportInstance, SubReport):

    rowFactory = MeetingMinutesWorkRow

    fields = Jeep((workTitle, party, deadline, state))   #description,
    defaultOutputFields = fields
    defaultSortCriteria = (day,)
    states = ('planned', 'accepted', 'running', 'done', 
                'finished', 'closed', 'moved')

    @property
    def queryCriteria(self):
        return CompoundQueryCriteria([])

    def selectObjects(self, parts):
        parts.pop('tasks', None)
        t = self.parentRow.context
        if t is not None:
            return self.selectWorkItems(t, parts)
        return []


eventTitle = CalculatedField('eventTitle', u'Event Title',
                description=u'',
                executionSteps=(['header']))
eventDescription = CalculatedField('eventDescription', u'Event Description',
                description=u'',
                executionSteps=(['header']))
eventDate = DateField('eventDate', u'Event Date',
                description=u'',
                format=('date', 'short'),
                executionSteps=(['header']))
eventStart = DateField('eventStart', u'Event Start',
                description=u'',
                format=('time', 'short'),
                executionSteps=(['header']))
eventEnd = DateField('eventEnd', u'Event End',
                description=u'',
                format=('time', 'short'),
                executionSteps=(['header']))
participants = CalculatedField('participants', u'Participants',
                description=u'',
                executionSteps=(['header']))
taskTitle = UrlField('title', u'Task Title',
                description=u'The short description of the task.',
                cssClass='header-1',
                executionSteps=['output'])
taskDescription = HtmlTextField('description', u'Description',
                description=u'The long description of the task.',
                cssClass='header-2',
                executionSteps=['output'])
responsible = TextField('responsible', u'label_responsible',
                description=u'Responsible.',
                cssClass='header-2',
                executionSteps=['output'])
discussion = HtmlTextField('discussion', u'label_discussion',
                description=u'Discussion.',
                cssClass='header-2',
                executionSteps=['output'])
consequences = HtmlTextField('consequences', u'label_consequences',
                description=u'Consequences.',
                cssClass='header-2',
                executionSteps=['output'])
workItems = SubReportField('workItems', u'Work Items',
                description=u'A list of work items belonging to the task.',
                reportFactory=MeetingMinutesWork,
                executionSteps=['output'])


class TaskRow(BaseRow):

    @Lazy
    def event(self):
        return self.parent.context.view.adapted

    @Lazy
    def eventTitle(self):
        return self.event.title

    @Lazy
    def eventDescription(self):
        return self.event.description

    @Lazy
    def eventDate(self):
        return self.event.start

    @Lazy
    def eventStart(self):
        return self.event.start

    @Lazy
    def eventEnd(self):
        return self.event.end

    @Lazy
    def participants(self):
        return self.event.participants

    useRowProperty = BaseRow.useRowProperty
    attributeHandlers = dict(
            eventDate=useRowProperty,
            eventStart=useRowProperty,
            eventEnd=useRowProperty,
    )


class MeetingMinutes(WorkReportInstance):

    type = "meeting_minutes"
    label = u'Meeting Minutes'

    rowFactory = TaskRow

    fields = Jeep((eventTitle, eventDate, eventStart, eventEnd, 
                   eventDescription, participants,
                   tasks, taskTitle, responsible, taskDescription, 
                   discussion, consequences, workItems))
    defaultOutputFields = fields
    states = ('planned', 'accepted', 'done', 'done_x', 'finished')
    taskTypeNames = ('agendaitem',)

    def selectObjects(self, parts):
        return [adapted(t) for t in self.getTasks(parts)[1:]]


