#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
View classes for export of report results.
"""

import csv
from cStringIO import StringIO
from zope.i18n import translate

from loops.common import normalizeName
from loops.expert.browser.report import ResultsConceptView
from loops.interfaces import ILoopsObject
from loops.util import _


class ResultsConceptCSVExport(ResultsConceptView):

    isToplevel = True
    reportMode = 'export'

    delimiter = ';'
    encoding = 'UTF-8'

    def getFileName(self):
        return normalizeName(self.context.title)

    def getColumnTitle(self, field):
        lang = self.languageInfo.language
        return translate(_(field.title), target_language=lang)

    def __call__(self):
        fields = self.displayedColumns
        fieldNames = [f.name for f in fields]
        output = StringIO()
        writer = csv.DictWriter(output, fieldNames, delimiter=self.delimiter)
        output.write(self.delimiter.join(
                        [self.getColumnTitle(f) for f in fields]) + '\n')
        results = self.reportInstance.getResults()
        for row in results:
            data = {}
            for f in fields:
                value = f.getValue(row)
                if ILoopsObject.providedBy(value):
                    value = value.title
                if isinstance(value, unicode):
                    value = value.encode(self.encoding)
                data[f.name] = value
            writer.writerow(data)
        text = output.getvalue()
        self.setDownloadHeader(text)
        return text

    def setDownloadHeader(self, text):
        response = self.request.response
        response.setHeader('Content-Disposition',
                           'attachment; filename=%s.csv' %
                                    self.getFileName())
        response.setHeader('Cache-Control', '')
        response.setHeader('Pragma', '')
        response.setHeader('Content-Type', 'text/csv')
        response.setHeader('Content-Length', len(text))
