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
Field definitions for reports.
"""

from cybertools.composer.report.field import Field
from cybertools.composer.report.result import ResultSet
from loops.common import baseObject
from loops.expert.report import ReportInstance
from loops import util


class TextField(Field):

    format = 'text/restructured'

    def getDisplayValue(self, row):
        value = self.getValue(row)
        return row.parent.context.view.renderText(value, self.format)


class UrlField(Field):

    renderer = 'target'

    def getDisplayValue(self, row):
        nv = row.parent.context.view.nodeView
        if row.context is None:     # probably a totals row
            return dict(title=u'', url=u'')
        return dict(title=self.getValue(row),
                    url=nv.getUrlForTarget(baseObject(row.context)))


class TargetField(Field):

    renderer = 'target'

    def getValue(self, row):
        value = self.getRawValue(row)
        if value is None:
            return None
        return util.getObjectForUid(value)

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if value is None:
            return dict(title=u'', url=u'')
        view = row.parent.context.view
        return dict(title=value.title, url=view.getUrlForTarget(value))


# sub-report stuff

class SubReport(ReportInstance):

    pass


class SubReportField(Field):

    renderer = 'subreport'
    reportFactory = SubReport

    def getReportInstance(self, row):
        baseReport = row.parent.context
        instance = self.reportFactory(baseReport.context)
        instance.view = baseReport.view
        return instance

    def getValue(self, row):
        ri = self.getReportInstance(row)
        return ResultSet(ri, ri.getResults())
