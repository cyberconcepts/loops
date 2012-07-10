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
Report type, report concept adapter, and other reporting stuff.
"""

from zope import schema, component
from zope.component import adapts
from zope.interface import Interface, Attribute, implements
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy

from cybertools.composer.report.base import Report as BaseReport
from cybertools.composer.report.base import LeafQueryCriteria, CompoundQueryCriteria
from cybertools.composer.report.interfaces import IReport as IBaseReport
from cybertools.composer.report.interfaces import IReportParams
from cybertools.composer.report.result import ResultSet, Row
from cybertools.util.jeep import Jeep
from loops.common import AdapterBase
from loops.interfaces import ILoopsAdapter
from loops.type import TypeInterfaceSourceList
from loops import util
from loops.util import _


# interfaces

class IReport(ILoopsAdapter, IReportParams):
    """ The report adapter for the persistent object (concept) that stores
        the report in the concept map.
    """

    reportType = schema.Choice(
        title=_(u'Report Type'),
        description=_(u'The type of the report.'),
        default=None,
        source='loops.expert.reportTypeSource',
        required=True)


class IReportInstance(IBaseReport):
    """ The report-type-specific object (an adapter on the report) that
        does the real report execution stuff.
    """


# report concept adapter and instances

class Report(AdapterBase):

    implements(IReport)

    _contextAttributes = list(IReport)

TypeInterfaceSourceList.typeInterfaces += (IReport,)


class ReportInstance(BaseReport):

    implements(IReportInstance)
    adapts(IReport)

    rowFactory = Row

    view = None     # set upon creation

    def __init__(self, context):
        self.context = context

    def getResultsRenderer(self, name, macros):
        return macros[name]

    @property
    def queryCriteria(self):
        return self.context.queryCriteria

    def getResults(self, dynaParams=None):
        crit = self.queryCriteria
        if crit is None:
            return []
        limits = self.limits
        if dynaParams is not None:
            for k, v in dynaParams.items():
                if k == 'limits':
                    limits = v
                    break
                if k in crit.parts.keys():
                    crit.parts[k].comparisonValue = v
        parts = Jeep(crit.parts)
        result = list(self.selectObjects(parts))  # may modify parts
        qc = CompoundQueryCriteria(parts)
        return ResultSet(self, result, rowFactory=self.rowFactory,
                         sortCriteria=self.getSortCriteria(), queryCriteria=qc,
                         limits=limits)

    def selectObjects(self, parts):
        # to be implemented by subclass
        return []

    @Lazy
    def conceptManager(self):
        return self.view.conceptManager

    @Lazy
    def recordManager(self):
        return self.view.loopsRoot.getRecordManager()

    @Lazy
    def hasReportPredicate(self):
        return self.conceptManager['hasreport']


class ReportTypeSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context

    def __iter__(self):
        return iter(self.reportTypes)

    def __contains__(self, value):
        return value in [item[0] for item in self]

    @Lazy
    def reportTypes(self):
        result = []
        for item in component.getAdapters([self.context], IReportInstance):
            name, adapter = item
            adapter = removeSecurityProxy(adapter)
            label = getattr(adapter, 'label', name)
            result.append((name, label,))
        return result

    def __len__(self):
        return len(self.reportTypes)


# default concept report

class DefaultConceptReportInstance(ReportInstance):

    label = u'Default Concept Report'

