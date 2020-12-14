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
View classes for reporting.
"""

from logging import getLogger
from urllib import urlencode
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getParent

from cybertools.browser.form import FormController
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted, AdapterBase
from loops.expert.report import IReportInstance
from loops.interfaces import IConcept
from loops.organize.personal.browser.filter import FilterView
from loops.security.common import canWriteObject, checkPermission
from loops import util
from loops.util import _


report_template = ViewPageTemplateFile('report.pt')
results_template = ViewPageTemplateFile('results.pt')


class ReportView(ConceptView):
    """ A view for defining (editing) a report.
    """

    resultsRenderer = None  # to be defined by subclass
    reportDownload = None
    reportName = None

    @Lazy
    def report_macros(self):
        return self.controller.mergeTemplateMacros('report', report_template)
        #return self.controller.getTemplateMacros('report', report_template)

    @Lazy
    def macro(self):
        return self.report_macros['main']

    @Lazy
    def tabTitle(self):
        return self.report.title

    @Lazy
    def dynamicParams(self):
        return self.request.form

    @Lazy
    def report(self):
        return self.adapted

    @Lazy
    def reportInstance(self):
        instance = component.getAdapter(self.report, IReportInstance,
                                        name=self.report.reportType)
        instance.view = self
        return instance

    @Lazy
    def queryFields(self):
        ri = self.reportInstance
        qf = ri.getAllQueryFields()
        if ri.userSettings:
            return [f for f in qf if f in ri.userSettings]
        return qf


class ResultsView(NodeView):

    @Lazy
    def result_macros(self):
        return self.controller.getTemplateMacros('results', results_template)

    @Lazy
    def macro(self):
        return self.result_macros['main']

    @Lazy
    def item(self):
        return self

    @Lazy
    def params(self):
        params = dict(self.request.form)
        params = self.parseParams(params)
        return params

    def parseParams(self, params):
        params.pop('report_execute', None)
        if 'limits' in params:
            params['limits'] = self.parseLimitsParam(params['limits'])
        return params

    def parseLimitsParam(self, value):
        if not value:
            return None
        if isinstance(value, basestring):
            limits = value.split(',')
        else:
            limits = value
        if len(limits) < 2:
            limits.append(None)
        result = []
        for p in limits[:2]:
            if not p:
                result.append(None)
            else:
                result.append(int(p))
        return result

    @Lazy
    def report(self):
        return adapted(self.virtualTargetObject)

    #@Lazy
    def results(self):
        return self.reportInstance.getResults(self.params)

    @Lazy
    def resultsRenderer(self):
        return self.reportInstance.getResultsRenderer('results', self.result_macros)

    @Lazy
    def reportUrl(self):
        url = self.virtualTargetUrl
        return '?'.join((url, urlencode(self.params)))

    @Lazy
    def displayedColumns(self):
        return self.reportInstance.getActiveOutputFields()

    def getColumnRenderer(self, col, name=None):
        return self.result_macros[col.renderer]


class ResultsConceptView(ConceptView):
    """ View on a concept using the results of a report.
    """

    logger = getLogger ('ResultsConceptView')

    reportName = None   # define in subclass if applicable
    reportDownload = None
    reportType = None   # set for using special report instance adapter

    def __init__(self, context, request):
        super(ResultsConceptView, self).__init__(context, request)
        self.resultSets = {}    # storage for result sets from reports

    @Lazy
    def result_macros(self):
        return self.controller.getTemplateMacros('results', results_template)

    @Lazy
    def resultsRenderer(self):
        return self.reportInstance.getResultsRenderer(
                                        'results', self.result_macros)

    @Lazy
    def macro(self):
        return self.result_macros['content']

    def reportDownloadTitle(self):
        return _(u'Download $title', mapping={'title': self.report.title})

    @Lazy
    def hasReportPredicate(self):
        return self.conceptManager['hasreport']

    @Lazy
    def reportName(self):
        rn = self.request.form.get('report_name')
        if rn is not None:
            return rn
        return (self.getOptions('report_name') or [None])[0]

    @Lazy
    def reportType(self):
        if IConcept.providedBy(self.context):
            return (self.getOptions('report_type') or [None])[0]

    @Lazy
    def report(self):
        if self.reportName:
            report = adapted(self.conceptManager.get(self.reportName))
            if report is None:
                self.logger.warn("Report '%s' not found." % self.reportName)
            return report
        reports = self.context.getParents([self.hasReportPredicate])
        if not reports:
            type = self.context.conceptType
            reports = type.getParents([self.hasReportPredicate])
        if reports:
            return adapted(reports[0])

    @Lazy
    def reportInstance(self):
        reportType = self.reportType or self.report.reportType
        ri = component.getAdapter(self.report, IReportInstance,
                                  name=reportType)
        ri.view = self
        if not ri.sortCriteria:
            si = self.sortInfo.get('results')
            if si is not None:
                fnames = (si['colName'],)
                ri.sortCriteria = [f for f in ri.getSortFields() 
                                     if f.name in fnames]
                ri.sortDescending = not si['ascending']
        return ri

    def results(self):
        res = self.reportInstance.getResults()
        self.resultSets[res.context.name] = res
        return res

    @Lazy
    def displayedColumns(self):
        return self.reportInstance.getActiveOutputFields()

    def getColumnRenderer(self, col, name=None):
        return self.result_macros[col.renderer]

    @Lazy
    def downloadLink(self, format='csv'):
        opt = self.options('download_' + format)
        if not opt:
            opt = self.typeOptions('download_' + format)
        if opt:
            return '/'.join((self.nodeView.virtualTargetUrl, opt[0]))

    @Lazy
    def reportDownload(self):
        return self.downloadLink

    def isSortableColumn(self, tableName, colName):
        if tableName == 'results':
            if colName in [f.name for f in self.reportInstance.getSortFields()]:
                return True
        return False


class EmbeddedResultsConceptView(ResultsConceptView):

    @Lazy
    def macro(self):
        return self.result_macros['embedded_content']

    @Lazy
    def title(self):
        return self.report.title


class ReportConceptView(ResultsConceptView, ReportView):
    """ View on a concept using a report.
    """

    def setupController(self):
        super(ReportConceptView, self).setupController()
        self.registerDojoDateWidget()

    @Lazy
    def macro(self):
        return self.report_macros['main']

    @Lazy
    def queryFields(self):
        ri = self.reportInstance
        qf = ri.getAllQueryFields()
        if ri.userSettings:
            return [f for f in qf if f in ri.userSettings]
        return qf


class EmbeddedReportConceptView(ReportConceptView):

    @Lazy
    def macro(self):
        return self.report_macros['embedded_report']

    @Lazy
    def title(self):
        return self.report.title


class ReportParamsView(ReportConceptView):
    """ Report view allowing to enter parameters before executing the report.
    """

    @Lazy
    def macro(self):
        return self.report_macros['main_params']
