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
from loops.common import adapted, baseObject
from loops.knowledge.browser import InstitutionMixin
from loops.knowledge.survey.response import Responses
from loops.organize.party import getPersonForUser
from loops.util import getObjectForUid
from loops.util import _


template = ViewPageTemplateFile('view_macros.pt')

class SurveyView(InstitutionMixin, ConceptView):

    data = None
    errors = None
    batchSize = 12
    teamData = None

    template = template

    adminMaySelectAllInstitutions = False

    @Lazy
    def macro(self):
        self.registerDojo()
        return template.macros['survey']

    @Lazy
    def title(self):
        title = self.context.title
        personId = self.request.form.get('person')
        if personId:
            person = adapted(getObjectForUid(personId))
            if person is not None:
                return '%s: %s' % (title, person.title)
        return title

    @Lazy
    def tabview(self):
        if self.editable:
            return 'index.html'

    def update(self):
        instUid = self.request.form.get('select_institution')
        if instUid:
            return self.setInstitution(instUid)

    @Lazy
    def groups(self):
        result = []
        if self.adapted.noGrouping:
            questions = list(self.adapted.questions)
            questions.sort(key=lambda x: x.title)
            size = len(questions)
            #nb, rem = divmod(size, self.batchSize)
            bs = self.batchSize
            for idx in range(0, size, bs):
                result.append(dict(title=u'Question', infoText=None, 
                                   questions=questions[idx:idx+bs]))
        else:
            for group in self.adapted.questionGroups:
                result.append(dict(title=group.title, 
                                   infoText=self.getInfoText(group),
                                   questions=group.questions))
        return result

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
        #personId = respManager.personId
        #person = self.getObjectForUid(personId)
        #inst = person.getParents([pred])
        inst = self.institution
        if inst:
            for c in inst.getChildren([pred]):
                uid = self.getUidForObject(c)
                data = respManager.load(uid)
                if data:
                    resp = Response(self.adapted, None)
                    for qu in self.adapted.questions:
                        if qu.questionType != 'value_selection':
                            continue
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
        respManager.personId = (self.request.form.get('person') or 
                                respManager.getPersonId())
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
            self.teamData = self.getTeamData(respManager)
            teamValues = response.getTeamResult(values, self.teamData)
            for idx, r in enumerate(teamValues):
                result[idx]['average'] = int(round(r['average'] * 100))
                result[idx]['teamRank'] = r['rank']
        return result

    def check(self, response):
        errors = []
        values = response.values
        for qu in self.adapted.questions:
            if qu.required and qu not in values:
                errors.append(dict(uid=qu.uid,
                    text='Please answer the obligatory questions.'))
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
                if self.adapted.noGrouping:
                    errors.append(dict(uid=qugroup.uid,
                        text='Please answer the highlighted questions.'))
                else:
                    errors.append(dict(uid=qugroup.uid,
                        text='Please answer the minimum number of questions.'))
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

    def loadData(self):
        if self.data is None:
            respManager = Responses(self.context)
            respManager.personId = (self.request.form.get('person') or 
                                    respManager.getPersonId())
            self.data = respManager.load()

    def getValues(self, question):
        setting = None
        self.loadData()
        if self.data:
            setting = self.data.get(question.uid)
        if setting is None:
            setting = 'none'
        setting = str(setting)
        result = []
        for opt in self.answerOptions:
            value = str(opt['value'])
            result.append(dict(value=value, checked=(setting == value), 
                               title=opt.get('description') or u''))
        return result

    def getTextValue(self, question):
        self.loadData()
        if self.data:
            return self.data.get(question.uid)

    def getCssClass(self, question):
        cls = ''
        if self.errors and self.data.get(question.uid) is None:
            cls = 'error '
        return cls + 'vpad'


class SurveyCsvExport(NodeView):

    encoding = 'ISO8859-15'

    def encode(self, text):
        return text.encode(self.encoding)

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
        infoCols = ['Institution', 'Name', 'Timestamp']
        dataCols = ['%02i-%02i' % (item[0], item[1]) for item in self.questions]
        return infoCols + dataCols

    def getRows(self):
        memberPred = self.conceptManager.get('ismember')
        for tr in Responses(self.virtualTargetObject).getAllTracks():
            p = adapted(getObjectForUid(tr.userName))
            name = self.encode(p and p.title or u'???')
            inst = u''
            if memberPred is not None:
                for i in baseObject(p).getParents([memberPred]):
                    inst = self.encode(i.title)
                    break
            ts = formatTimeStamp(tr.timeStamp)
            cells = [tr.data.get(qu.uid, -1) 
                        for (idx1, idx2, qug, qu) in self.questions]
            yield [inst, name, ts] + cells

    def __call__(self):
        f = StringIO()
        writer = csv.writer(f, delimiter=',')
        writer.writerow(self.columns)
        for row in sorted(self.getRows()):
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

