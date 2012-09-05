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

from zope.app.form.browser.interfaces import ITerms
from zope import component
from zope.i18n.locales import locales
from zope.schema.interfaces import IVocabularyFactory, IContextSourceBinder

from cybertools.composer.report.field import Field as BaseField
from cybertools.composer.report.field import TableCellStyle
from cybertools.composer.report.result import ResultSet
from cybertools.stateful.interfaces import IStateful, IStatesDefinition
from cybertools.util.date import timeStamp2Date
from loops.common import baseObject
from loops.expert.report import ReportInstance
from loops import util


class Field(BaseField):

    def getSelectValue(self, row):
        return self.getValue(row)


class TextField(Field):

    format = 'text/restructured'

    def getDisplayValue(self, row):
        value = self.getValue(row)
        text = row.parent.context.view.renderText(value, self.format)
        text = self.removeTopSpacing(text)
        return text

    def removeTopSpacing(self, text):
        styleInfo = u' style="margin-top: 0"'
        for tag in (u'<p', u'<ol', u'<ul'):
            if text.startswith(tag):
                text = tag + styleInfo + text[len(tag):]
                break
        return text


class DecimalField(Field):

    format = 'decimal'
    pattern = u'#,##0.00;-#,##0.00'
    renderer = cssClass = 'right'
    styleData = {'text-align':'right'}
    styleData = dict(Field.style.data, **styleData)
    style = TableCellStyle(**styleData)
    cssClass = 'number'

    def getDisplayValue(self, row):
        value = self.getRawValue(row)
        if not value:
            return u''
        if not isinstance(value, float):
            value = float(value)
        nv = row.parent.context.view.nodeView
        langInfo = nv and getattr(nv, 'languageInfo', None) or None
        if langInfo:
            locale = locales.getLocale(langInfo.language)
            fmt = locale.numbers.getFormatter(self.format)
            return fmt.format(value, pattern=self.pattern)
        return '%.2f' % value


class IntegerField(Field):
    
    renderer = cssClass = 'right'

    def getSortValue(self, row):
        value = self.getValue(row)
        if value.isdigit():
            return int(value)


class DateField(Field):

    format = ('date', 'short')
    renderer = cssClass = 'center'

    def getDisplayValue(self, row):
        value = self.getRawValue(row)
        if not value:
            return u''
        if isinstance(value, int):
            value = timeStamp2Date(value)
        nv = row.parent.context.view.nodeView
        langInfo = nv and getattr(nv, 'languageInfo', None) or None
        if langInfo:
            locale = locales.getLocale(langInfo.language)
            fmt = locale.dates.getFormatter(*self.format)
            return fmt.format(value)
        else:
            return value.isoformat()[:10]


class StateField(Field):

    statesDefinition = 'workItemStates'
    renderer = 'state'

    def getDisplayValue(self, row):
        if IStateful.providedBy(row.context):
            stf = row.context
        else:
            stf = component.getAdapter(row.context, IStateful, 
                                        name=self.statesDefinition)
        stateObject = stf.getStateObject()
        icon = stateObject.icon or 'led%s.png' % stateObject.color
        return dict(title=util._(stateObject.title), 
                    icon='cybertools.icons/' + icon)


class VocabularyField(Field):

    vocabulary = None

    def getDisplayValue(self, row):
        value = self.getRawValue(row)
        if self.vocabulary is None:
            return value
        items = self.getVocabularyItems(row)
        for item in items:
            if str(item['token']) == str(value):
                return item['title']

    def getVocabularyItems(self, row):
        context = row.context
        request = row.parent.context.view.request
        voc = self.vocabulary
        if isinstance(voc, basestring):
            terms = self.getVocabularyTerms(voc, context, request)
            if terms is not None:
                return terms
            voc = voc.splitlines()
            return [dict(token=t, title=t) for t in voc if t.strip()]
        elif IContextSourceBinder.providedBy(voc):
            source = voc(row.parent.context)
            terms = component.queryMultiAdapter((source, request), ITerms)
            if terms is not None:
                termsList = [terms.getTerm(value) for value in source]
                return [dict(token=t.token, title=t.title) for t in termsList]
            else:
                return []
        return [dict(token=t.token, title=t.title or t.value) for t in voc]

    def getVocabularyTerms(self, name, context, request):
        if context is None or request is None:
            return None
        source = component.queryUtility(IVocabularyFactory, name=name)
        if source is not None:
            source = source(context)
            terms = component.queryMultiAdapter((source, request), ITerms)
            if terms is not None:
                termsList = [terms.getTerm(value) for value in source]
                return [dict(token=t.token, title=t.title) for t in termsList]
        return None


class UrlField(Field):

    renderer = 'target'

    def getDisplayValue(self, row):
        if row.context is None:     # probably a totals row
            return dict(title=u'', url=u'')
        nv = row.parent.context.view.nodeView
        return dict(title=self.getValue(row),
                    url=nv.getUrlForTarget(baseObject(row.context)))


class IntegerUrlField(IntegerField, UrlField):

    renderer = 'target'


class RelationField(Field):

    renderer = 'target'
    displayAttribute = 'title'

    def getValue(self, row):
        return self.getRawValue(row)

    def getSortValue(self, row):
        return self.getDisplayValue(row)['title']

    def getDisplayValue(self, row):
        value = self.getValue(row)
        if not value:
            return dict(title=u'', url=u'')
        nv = row.parent.context.view.nodeView
        return dict(title=getattr(value, self.displayAttribute),
                    url=nv.getUrlForTarget(baseObject(value)))


class TargetField(RelationField):

    def getValue(self, row):
        value = self.getRawValue(row)
        if value is None:
            return None
        return util.getObjectForUid(value)


class MultiLineField(Field):

    renderer = 'multiline'

    def getValue(self, row):
        return self.getRawValue(row)

    def getDisplayValues(self, row):
        value = self.getValue(row)
        if not isinstance(value, (list, tuple)):
            value = [value]
        return value


# sub-report stuff
class SubReport(ReportInstance):

    pass


class SubReportField(Field):

    template = None
    renderer = 'subreport'
    reportFactory = SubReport

    def getReportInstance(self, row):
        baseReport = row.parent.context
        instance = self.reportFactory(baseReport.context)
        instance.view = baseReport.view
        instance.parentRow = row
        return instance

    def getValue(self, row):
        ri = self.getReportInstance(row)
        rs = ri.getResults()
        ri.view.resultSets[ri.name] = rs
        return rs
    
