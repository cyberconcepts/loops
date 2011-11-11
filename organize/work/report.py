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
from cybertools.util.jeep import Jeep
from loops.expert.report import ReportInstance

results_template = ViewPageTemplateFile('results.pt')


task = Field('task', u'Task',
                description=u'The task to which work items belong.',
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
    fields = Jeep((day, dayFrom, dayTo, task, work, workDescription))
    defaultOutputFields = fields

    @Lazy
    def queryCriteria(self):
        # TODO: take from persistent report where appropriate
        crit = [LeafQueryCriteria(f.name, f.operator, None, f)
                    for f in self.getAllQueryFields()]
        return CompoundQueryCriteria(crit)

    def getResultsRenderer(self, name, defaultMacros):
        return results_template.macros[name]

    def selectObjects(self, parts):
        task = parts.get('task')
        if not task:
            return []
        return []

