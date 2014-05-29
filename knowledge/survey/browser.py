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

    @Lazy
    def answerOptions(self):
        opts = self.adapted.answerOptions
        if not opts:
            opts = [
                dict(value='none', label=u'No answer', 
                        description=u'survey_value_none'),
                dict(value=3, label=u'Fully applies', 
                        description=u'survey_value_3'),
                dict(value=2, label=u'', description=u'survey_value_2'),
                dict(value=1, label=u'', description=u'survey_value_1'),
                dict(value=0, label=u'Does not apply', 
                        description=u'survey_value_0'),]
        return opts

    @Lazy
    def showFeedbackText(self):
        sft = self.adapted.showFeedbackText
        return sft is None and True or sft

    @Lazy
    def feedbackColumns(self):
        cols = self.adapted.feedbackColumns
        if not cols:
            cols = [
                dict(name='text', label=u'Response'),
                dict(name='score', label=u'Score')]
        return cols

    @Lazy
    def showTeamResults(self):
        for c in self.feedbackColumns:
            if c['name'] in ('average', 'teamRank'):
                return True
        return False

    def getTeamData(self, respManager):
        result = []
        pred = self.conceptManager.get('ismember')
        if pred is None:
            return result
        personId = respManager.personId
        person = self.getObjectForUid(personId)
        inst = person.getParents([pred])
        if inst:
            for c in inst[0].getChildren([pred]):
                uid = self.getUidForObject(c)
                data = respManager.load(uid)
                if data:
                    resp = Response(self.adapted, None)
                    for qu in self.adapted.questions:
                        if qu.uid in data:
                            resp.values[qu] = data[qu.uid]
                    qgAvailable = True
                    for qg in self.adapted.questionGroups:
                        if qg.uid in data:
                            resp.values[qg] = data[qg.uid]
                        else:
                            qgAvailable = False
                    if not qgAvailable:
                        values = resp.getGroupedResult()
                        for v in values:
                            resp.values[v['group']] = v['score']
                    result.append(resp)
        return result

    def results(self):
        form = self.request.form
        if 'submit' not in form:
            return []
        respManager = Responses(self.context)
        data = {}
        response = Response(self.adapted, None)
        for key, value in form.items():
            if key.startswith('question_'):
                if value != 'none':
                    uid = key[len('question_'):]
                    question = adapted(self.getObjectForUid(uid))
                    if value.isdigit():
                        value = int(value)
                    data[uid] = value
                    response.values[question] = value
        values = response.getGroupedResult()
        for v in values:
            data[self.getUidForObject(v['group'])] = v['score']
        respManager.save(data)
        self.data = data
        self.errors = self.check(response)
        if self.errors:
            return []
        result = [dict(category=r['group'].title, text=r['feedback'].text, 
                       score=int(round(r['score'] * 100)), rank=r['rank']) 
                    for r in values]
        if self.showTeamResults:
            teamData = self.getTeamData(respManager)
            teamValues = response.getTeamResult(values, teamData)
            for idx, r in enumerate(teamValues):
                result[idx]['average'] = int(round(r['average'] * 100))
                result[idx]['teamRank'] = r['rank']
        return result

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
            info = translate(_(u'Please answer all questions.'), 
                target_language=lang)
        elif qugroup.minAnswers > 0:
            info = translate(_(u'Please answer at least $minAnswers questions.',
                               mapping=dict(minAnswers=qugroup.minAnswers)),
                             target_language=lang)
        if info:
            text = u'<i>%s</i><br />(%s)' % (text, info)
        return text

    def getValues(self, question):
        setting = None
        if self.data is None:
            self.data = Responses(self.context).load()
        if self.data:
            setting = self.data.get(question.uid)
        if setting is None:
            setting = 'none'
        setting = str(setting)
        result = []
        for opt in self.answerOptions:
            value = str(opt['value'])
            result.append(dict(value=value, checked=(setting == value)))
        return result
      
        #noAnswer = [dict(value='none', checked=(setting == None),
        #                 radio=(not question.required))]
        #return noAnswer + [dict(value=i, checked=(setting == i), radio=True) 
        #                        for i in reversed(range(question.answerRange))]


class SurveyCsvExport(NodeView):

    encoding = 'ISO8859-15'

    def encode(self, text):
        text.encode(self.encoding)

    @Lazy
    def questions(self):
        result = []
        for idx1, qug in enumerate(
                    adapted(self.virtualTargetObject).questionGroups):
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

