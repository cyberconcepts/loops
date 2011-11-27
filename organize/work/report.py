#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
from loops.expert.report import ReportInstance
from loops import util

results_template = ViewPageTemplateFile('results.pt')


class TargetField(Field):

    renderer = 'target'

    def getValue(self, row):
        value = self.getRawValue(row)
        return util.getObjectForUid(value)

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if value is None:
            return dict(title=self.getRawValue(row), url=u'')
        view = row.parent.context.view
        return dict(title=value.title, url=view.getUrlForTarget(value))


class DayField(Field):

    def getValue(self, row):
        return timeStamp2Date(self.getRawValue(row))

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if value:
            view = row.parent.context.view
            return formatDate(value, 'date', 'short', view.languageInfo.language)
        return u''


tasks = Field('tasks', u'Tasks',
                description=u'The tasks from which work items should be selected.',
                executionSteps=['query'])
dayFrom = Field('dayFrom', u'Start Day',
                description=u'The first day from which to select work.',
                executionSteps=['query'])
dayTo = Field('dayTo', u'End Day',
                description=u'The last day until which to select work.',
                executionSteps=['query'])
day = DayField('day', u'Day',
                description=u'The day the work was done.',
                executionSteps=['sort', 'output'])
timeStart = Field('start', u'Start Time',
                description=u'The time the unit of work was started.',
                executionSteps=['sort', 'output'])
timeEnd = Field('end', u'End Time',
                description=u'The time the unit of work was finished.',
                executionSteps=['output'])
task = TargetField('taskId', u'Task',
                description=u'The task to which work items belong.',
                executionSteps=['output'])
party = TargetField('userName', u'Party',
                description=u'The party (usually a person) who did the work.',
                executionSteps=['sort', 'output'])
title = Field('title', u'Title',
                description=u'The short description of the work.',
                executionSteps=['output'])
description = Field('description', u'Description',
                description=u'The long description of the work.',
                executionSteps=['x_output'])
duration = Field('duration', u'Duration',
                description=u'The duration of the work.',
                executionSteps=['output'])
effort = Field('effort', u'Effort',
                description=u'The effort of the work.',
                executionSteps=['output', 'sum'])
state = Field('state', u'State',
                description=u'The state of the work.',
                executionSteps=['query', 'output'])


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

    attributeHandlers = dict(day=getDay)


class WorkReportInstance(ReportInstance):

    type = "deliverables"
    label = u'Work Report'

    rowFactory = WorkRow
    fields = Jeep((dayFrom, dayTo, tasks,
                   day, timeStart, timeEnd, task, party, title, description,
                   duration, effort, state))
    defaultOutputFields = fields

    @property
    def queryCriteria(self):
        crit = self.context.queryCriteria
        if crit is None:
            f = self.fields['tasks']
            tasks = baseObject(self.context).getChildren([self.hasReportPredicate])
            crit = [LeafQueryCriteria(f.name, f.operator, tasks, f)]
        return CompoundQueryCriteria(crit)

    def getResultsRenderer(self, name, defaultMacros):
        return results_template.macros[name]

    def selectObjects(self, parts):
        result = []
        tasks = parts.pop('tasks').comparisonValue
        for t in list(tasks):
            tasks.extend(self.getAllSubtasks(t))
        for t in tasks:
            result.extend(self.selectWorkItems(t, parts))
        # TODO: remove parts already used for selection from parts list
        return result

    def selectWorkItems(self, task, parts):
        wi = self.workItems
        states = ['done', 'done_x', 'finished']
        return wi.query(task=util.getUidForObject(task), state=states)

    def getAllSubtasks(self, concept):
        result = []
        for c in concept.getChildren():
            if c.conceptType == self.taskType:
                result.append(c)
            result.extend(self.getAllSubtasks(c))
        return result

    @Lazy
    def taskType(self):
        return self.conceptManager['task']

    @Lazy
    def workItems(self):
        return IWorkItems(self.recordManager['work'])
