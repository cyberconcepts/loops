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
from cybertools.util.jeep import Jeep
from loops.common import adapted, baseObject
from loops.expert.report import ReportInstance
from loops import util

results_template = ViewPageTemplateFile('results.pt')


tasks = Field('tasks', u'Tasks',
                description=u'The tasks to which work items belong.',
                executionSteps=['query', 'output', 'sort'])
work = Field('work', u'Work',
                description=u'The short description of the work.',
                executionSteps=['output'])
workDescription = Field('workDescription', u'Work Description',
                description=u'The long description of the work.',
                executionSteps=['output'])
day = Field('day', u'Day',
                description=u'The day the work was done.',
                executionSteps=['output', 'sort'])
dayFrom = Field('dayFrom', u'Start Day',
                description=u'The first day from which to select work.',
                executionSteps=['query'])
dayTo = Field('dayTo', u'End Day',
                description=u'The last day until which to select work.',
                executionSteps=['query'])


class WorkRow(BaseRow):

    pass


class WorkReportInstance(ReportInstance):

    type = "deliverables"
    label = u'Work Report'

    rowFactory = WorkRow
    fields = Jeep((day, dayFrom, dayTo, tasks, work, workDescription))
    defaultOutputFields = fields

    @property
    def queryCriteria(self):
        crit = self.context.queryCriteria
        if crit is None:
            f = self.fields['tasks']
            tasks = baseObject(self.context).getChildren([self.hasReportPredicate])
            crit = [LeafQueryCriteria(f.name, f.operator, tasks, f)]
        return CompoundQueryCriteria(crit)

    @property
    def xx_queryCriteria(self):
        crit = [LeafQueryCriteria(f.name, f.operator, None, f)
                    for f in self.getAllQueryFields()]
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
        return wi.query(task=util.getUidForObject(task))

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
