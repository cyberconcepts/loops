#
#  Copyright (c) 2017 Helmut Merz helmutm@cy55.de
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
import os
import time
from zope.cachedescriptors.property import Lazy
from zope.i18n import translate
from zope.i18nmessageid import Message
from zope.traversing.api import getName

from cybertools.meta.interfaces import IOptions
from cybertools.util.date import formatTimeStamp
from loops.common import normalizeName
from loops.expert.browser.report import ResultsConceptView
from loops.interfaces import ILoopsObject
from loops.util import _, getVarDirectory


class ResultsConceptCSVExport(ResultsConceptView):

    isToplevel = True
    reportMode = 'export'

    delimiter = ';'
    #encoding = 'UTF-8'
    #encoding = 'ISO8859-15'
    #encoding = 'CP852'

    @Lazy
    def encoding(self):
        enc = self.globalOptions('csv_encoding')
        if enc:
            return enc[0]
        return 'UTF-8'

    def getFileName(self):
        return normalizeName(self.context.title)

    def getColumnTitle(self, field):
        lang = self.languageInfo.language
        title = field.title
        if not isinstance(title, Message):
            title = _(title)
        #return translate(_(field.title), target_language=lang)
        return encode(translate(title, target_language=lang), 
                      self.encoding)

    def getFilepaths(self, name):
        repName = getName(self.report.context)
        ts = formatTimeStamp(None, format='%y%m%d%H%M%S')
        name = '-'.join((ts, repName))
        return (name + '.csv', 
                name + '.xlsx', 
                repName + '.ods')

    def renderCsv(self, name, src, tgt, tpl):
        callable = os.path.join('~', 'bin', name)
        command = ' '.join((callable, src, tgt, tpl))
        #print '***', command
        os.popen(command).read()

    def __call__(self):
        fields = self.displayedColumns
        fieldNames = [f.name for f in fields]
        csvRenderer = IOptions(self.report)('csv_renderer')
        if not csvRenderer:
            csvRenderer = self.globalOptions('csv_renderer')
        if csvRenderer:
            csvRenderer = csvRenderer[0]
            outfn, inpfn, tplfn = self.getFilepaths(csvRenderer)
            outpath = os.path.join(getVarDirectory(), 'export', 'excel', outfn)
            inpath = os.path.join(getVarDirectory(), 'export', 'excel', inpfn)
            output = open(outpath, 'w')
        else:
            output = StringIO()
        writer = csv.DictWriter(output, fieldNames, delimiter=self.delimiter)
        output.write(self.delimiter.join(
                        [self.getColumnTitle(f) for f in fields]) + '\n')
        results = self.reportInstance.getResults()
        for row in results:
            data = {}
            for f in fields:
                lang = self.languageInfo.language
                value = f.getExportValue(row, 'csv', lang)
                if ILoopsObject.providedBy(value):
                    value = value.title
                value = encode(value, self.encoding)
                data[f.name] = value
            writer.writerow(data)
        if csvRenderer:
            output.close()
            self.renderCsv(csvRenderer, outfn, inpfn, tplfn)
            input = open(inpath, 'rb')
            text = input.read()
            input.close()
            self.setDownloadHeader(text)
                #'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                #'xlsx')
        else:
            text = output.getvalue()
            self.setDownloadHeader(text)
        return text

    def setDownloadHeader(self, text, ctype='text/csv', ext='csv'):
        response = self.request.response
        response.setHeader('Content-Disposition',
                           'attachment; filename=%s.%s' %
                                (self.getFileName(), ext))
        response.setHeader('Cache-Control', '')
        response.setHeader('Pragma', '')
        response.setHeader('Content-Type', ctype)
        response.setHeader('Content-Length', len(text))


def encode(text, encoding):
    if not isinstance(text, unicode):
        return text
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        result = []
        for c in text:
            try:
                result.append(c.encode(encoding))
            except UnicodeEncodeError:
                result.append('?')
        return ''.join(result)
    return '???'

