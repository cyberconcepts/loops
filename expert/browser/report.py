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
View classes for reporting.
"""

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
from loops.organize.personal.browser.filter import FilterView
from loops.security.common import canWriteObject, checkPermission
from loops import util
from loops.util import _


report_template = ViewPageTemplateFile('report.pt')
results_template = ViewPageTemplateFile('results.pt')


class ReportView(ConceptView):

    @Lazy
    def report_macros(self):
        return self.controller.getTemplateMacros('report', report_template)

    @Lazy
    def macro(self):
        return self.report_macros['main']

    @Lazy
    def dynamicParams(self):
        return self.request.form


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
        params.pop('report_execute', None)
        return params

    @Lazy
    def report(self):
        return adapted(self.virtualTargetObject)

    @Lazy
    def reportInstance(self):
        instance = component.getAdapter(self.report, IReportInstance,
                                        name=self.report.reportType)
        instance.view = self
        return instance

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

    def getColumnRenderer(self, name):
        return self.result_macros[name]
