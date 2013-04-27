#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff for 
surveys and self-assessments.
"""

import csv
from cStringIO import StringIO
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.i18n import translate

from cybertools.knowledge.survey.questionnaire import Response
from cybertools.util.date import formatTimeStamp
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted
from loops.knowledge.survey.response import Responses
from loops.organize.party import getPersonForUser
from loops.util import getObjectForUid
from loops.util import _


template = ViewPageTemplateFile('view_macros.pt')

class SurveyView(ConceptView):

    data = None
    errors = None

    @Lazy
    def macro(self):
        self.registerDojo()
        return template.macros['survey']

    @Lazy
    def tabview(self):
        if self.editable:
            return 'index.html'

    def results(self):
        result = []
        response = None
        form = self.request.form
        if 'submit' in form:
            self.data = {}
            response = Response(self.adapted, None)
            for key, value in form.items():
                if key.startswith('question_'):
                    uid = key[len('question_'):]
                    question = adapted(self.getObjectForUid(uid))
                    if value != 'none':
                        value = int(value)
                        self.data[uid] = value
                        response.values[question] = value
            Responses(self.context).save(self.data)
            self.errors = self.check(response)
            if self.errors:
                return []
        if response is not None:
            result = response.getGroupedResult()
        return [dict(category=r[0].title, text=r[1].text, 
                            score=int(round(r[2] * 100)))
                        for r in result]

    def check(self, response):
        errors = []
        values = response.values
        for qu in self.adapted.questions:
            if qu.required and qu not in values:
                errors.append('Please answer the obligatory questions.')
                break
        qugroups = {}
        for qugroup in self.adapted.questionGroups:
            qugroups[qugroup] = 0
        for qu in values:
            qugroups[qu.questionGroup] += 1
        for qugroup, count in qugroups.items():
            minAnswers = qugroup.minAnswers
            if minAnswers in (u'', None):
                minAnswers = len(qugroup.questions)
            if count < minAnswers:
                errors.append('Please answer the minimum number of questions.')
                break
        return errors

    def getInfoText(self, qugroup):
        lang = self.languageInfo.language
        text = qugroup.description
        info = None
        if qugroup.minAnswers in (u'', None):
            info = translate(_(u'Please answer all questions.'), target_language=lang)
        elif qugroup.minAnswers > 0:
            info = translate(_(u'Please answer at least $minAnswers questions.',
                               mapping=dict(minAnswers=qugroup.minAnswers)),
                             target_language=lang)
        if info:
            text = u'%s<br />(%s)' % (text, info)
        return text

    def getValues(self, question):
        setting = None
        if self.data is None:
            self.data = Responses(self.context).load()
        if self.data:
            setting = self.data.get(question.uid)
        noAnswer = [dict(value='none', checked=(setting == None),
                         radio=(not question.required))]
        return noAnswer + [dict(value=i, checked=(setting == i), radio=True) 
                                for i in reversed(range(question.answerRange))]


class SurveyCsvExport(NodeView):

    encoding = 'ISO8859-15'

    def encode(self, text):
        text.encode(self.encoding)

    @Lazy
    def questions(self):
        result = []
        for idx1, qug in enumerate(adapted(self.virtualTargetObject).questionGroups):
            for idx2, qu in enumerate(qug.questions):
                result.append((idx1, idx2, qug, qu))
        return result

    @Lazy
    def columns(self):
        infoCols = ['Name', 'Timestamp']
        dataCols = ['%02i-%02i' % (item[0], item[1]) for item in self.questions]
        return infoCols + dataCols

    def getRows(self):
        for tr in Responses(self.virtualTargetObject).getAllTracks():
            p = adapted(getObjectForUid(tr.userName))
            name = p and p.title or u'???'
            ts = formatTimeStamp(tr.timeStamp)
            cells = [tr.data.get(qu.uid, -1) 
                        for (idx1, idx2, qug, qu) in self.questions]
            yield [name, ts] + cells

    def __call__(self):
        f = StringIO()
        writer = csv.writer(f, delimiter=',')
        writer.writerow(self.columns)
        for row in self.getRows():
            writer.writerow(row)
        text = f.getvalue()
        self.setDownloadHeader(text)
        return text

    def setDownloadHeader(self, text):
        response = self.request.response
        filename = 'survey_data.csv'
        response.setHeader('Content-Disposition',
                               'attachment; filename=%s' % filename)
        response.setHeader('Cache-Control', '')
        response.setHeader('Pragma', '')
        response.setHeader('Content-Length', len(text))
        response.setHeader('Content-Type', 'text/csv')

