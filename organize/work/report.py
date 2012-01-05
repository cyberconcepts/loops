#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapter

from cybertools.composer.report.base import Report
from cybertools.composer.report.base import LeafQueryCriteria, CompoundQueryCriteria
from cybertools.composer.report.field import Field
from cybertools.composer.report.result import ResultSet, Row as BaseRow
from cybertools.organize.interfaces import IWorkItems
from cybertools.util.date import timeStamp2Date
from cybertools.util.format import formatDate
from cybertools.util.jeep import Jeep
from loops.common import adapted, baseObject
from loops.expert.field import TargetField, TextField, UrlField, SubReportField
from loops.expert.report import ReportInstance
from loops import util


class DateField(Field):

    part = 'date'
    format = 'short'
    renderer = 'right'

    def getValue(self, row):
        value = self.getRawValue(row)
        if value is None:
            return None
        return timeStamp2Date(value)

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if value:
            view = row.parent.context.view
            return formatDate(value, self.part, self.format,
                              view.languageInfo.language)
        return u''


class TimeField(DateField):

    part = 'time'


class DurationField(Field):

    renderer = 'right'

    def getValue(self, row):
        value = self.getRawValue(row)
        if value and 'totals' in self.executionSteps:
            data = row.parent.totals.data
            data[self.name] = data.get(self.name, 0) + value
        if value:
            value /= 3600.0
        return value

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if not value:
            return u''
        return u'%02i:%02i' % divmod(value * 60, 60)


# common fields

tasks = Field('tasks', u'Tasks',
                description=u'The tasks from which sub-tasks and '
                        u'work items should be selected.',
                executionSteps=['query'])

# work report fields

dayFrom = Field('dayFrom', u'Start Day',
                description=u'The first day from which to select work.',
                executionSteps=['query'])
dayTo = Field('dayTo', u'End Day',
                description=u'The last day until which to select work.',
                executionSteps=['query'])
day = DateField('day', u'Day',
                description=u'The day the work was done.',
                executionSteps=['sort', 'output'])
timeStart = TimeField('start', u'Start',
                description=u'The time the unit of work was started.',
                executionSteps=['sort', 'output'])
timeEnd = TimeField('end', u'End',
                description=u'The time the unit of work was finished.',
                executionSteps=['output'])
task = TargetField('taskId', u'Task',
                description=u'The task to which work items belong.',
                executionSteps=['output'])
party = TargetField('userName', u'Party',
                description=u'The party (usually a person) who did the work.',
                executionSteps=['query', 'sort', 'output'])
workTitle = Field('title', u'Title',
                description=u'The short description of the work.',
                executionSteps=['output'])
workDescription = Field('description', u'Description',
                description=u'The long description of the work.',
                executionSteps=['output'])
duration = DurationField('duration', u'Duration',
                description=u'The duration of the work.',
                executionSteps=['output'])
effort = DurationField('effort', u'Effort',
                description=u'The effort of the work.',
                executionSteps=['output', 'totals'])
state = Field('state', u'State',
                description=u'The state of the work.',
                executionSteps=['query', 'output'])

# task/event report fields

taskTitle = UrlField('title', u'Title',
                description=u'The short description of the task.',
                executionSteps=['output'])
taskDescription = TextField('description', u'Description',
                description=u'The long description of the task.',
                executionSteps=['output'])
workItems = SubReportField('workItems', u'Work Items',
                description=u'A list of work items belonging to the task.',
                executionSteps=['output'])


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

    attributeHandlers = dict(day=getDay, duration=getDuration, effort=getEffort)


class WorkReportInstance(ReportInstance):

    type = "work_statement"
    label = u'Work Statement'

    rowFactory = WorkRow

    fields = Jeep((dayFrom, dayTo, tasks,
                   day, timeStart, timeEnd, task, party, workTitle, #description,
                   duration, effort, state))

    defaultOutputFields = fields
    defaultSortCriteria = (day, timeStart,)
    states = ('done', 'done_x', 'finished')
    taskTypeNames = ('task', 'event', 'project')

    @property
    def queryCriteria(self):
        form = self.view.request.form
        crit = self.context.queryCriteria or []
        if not crit and 'tasks' not in form:
            f = self.fields['tasks']
            tasks = baseObject(self.context).getChildren([self.hasReportPredicate])
            tasks = [util.getUidForObject(task) for task in tasks]
            crit = [LeafQueryCriteria(f.name, f.operator, tasks, f)]
        for f in self.getAllQueryFields():
            if f.name in form:
                crit.append(LeafQueryCriteria(f.name, f.operator, form[f.name], f))
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

    def getAllSubtasks(self, concept):
        result = []
        for c in concept.getChildren():
            if c.conceptType in self.taskTypes:
                result.append(c)
            result.extend(self.getAllSubtasks(c))
        return result

    def selectWorkItems(self, task, parts):
        # TODO: take states from parts
        kw = dict(task=util.getUidForObject(task), state=self.states)
        if 'userName' in parts:
            kw['userName'] = parts['userName'].comparisonValue
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


# meeting minutes

class TaskRow(BaseRow):

    pass


class MeetingMinutes(WorkReportInstance):

    # TODO:
    # header (event) fields: title, description, from/to,
    #               location, participants (or put in description?)
    # result set field for work items
    # work item fields: title, description, party, deadline, state

    type = "meeting_minutes"
    label = u'Meeting Minutes'

    rowFactory = TaskRow

    fields = Jeep((tasks, taskTitle, taskDescription, workItems))
    defaultOutputFields = fields
    states = ('planned', 'accepted', 'done', 'done_x', 'finished')

    def selectObjects(self, parts):
        return self.getTasks(parts)[1:]

