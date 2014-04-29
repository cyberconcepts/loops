#
#  Copyright (c) 2014 Helmut Merz helmutm@cy55.de
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
Qualification management report definitions.
"""

from zope.cachedescriptors.property import Lazy

from cybertools.util.jeep import Jeep
from loops.expert.report import ReportInstance
from loops.organize.work.report import WorkRow
from loops.organize.work.report import deadline, day, task, party, state
from loops.organize.work.report import workTitle, workDescription
from loops import util


class QualificationOverview(ReportInstance):

    type = "qualification_overview"
    label = u'Qualification Overview'

    rowFactory = WorkRow

    fields = Jeep((task, party, workTitle, day, state)) # +deadline?

    defaultOutputFields = fields

    def getOptions(self, option):
        return self.view.options(option)

    @Lazy
    def states(self):
        return self.getOptions('report_select_state' or ('planned',))

    def selectObjects(self, parts):
        result = []
        workItems = self.recordManager['work']
        pred = self.conceptManager['querytarget']
        types = self.view.context.getChildren([pred])
        for t in types:
            for c in t.getChildren([self.view.typePredicate]):
                uid = util.getUidForObject(c)
                for wi in workItems.query(taskId=uid, state=self.states):
                    result.append(wi)
        return result
