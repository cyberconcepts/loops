# loops.knowledge.survey.browser

""" Definition of view classes and other browser related stuff for 
surveys and self-assessments.
"""

import csv
from io import StringIO
import math
from zope.browserpage import ViewPageTemplateFile
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
from loops.security.common import checkPermission
from loops.util import getObjectForUid
from loops.util import _


template = ViewPageTemplateFile('view_macros.pt')

class SurveyView(InstitutionMixin, ConceptView):

    data = None
    errors = message = None
    batchSize = 12
    teamData = None

    template = template

    #adminMaySelectAllInstitutions = False

    @Lazy
    def macro(self):
        self.registerDojo()
        return template.macros['survey']

    @Lazy
    def title(self):
        title = self.context.title
        if self.personId:
            person = adapted(getObjectForUid(self.personId))
            if person is not None:
                return '%s: %s' % (title, person.title)
        return title

    @Lazy
    def tabview(self):
        if self.editable:
            return 'index.html'

    def getUrlParamString(self):
        qs = super(SurveyView, self).getUrlParamString()
        if qs.startswith('?report='):
            return ''
        return qs

    @Lazy
    def personId(self):
        return self.request.form.get('person')

    @Lazy
    def report(self):
        return self.request.form.get('report')

    @Lazy
    def questionnaireType(self):
        return self.adapted.questionnaireType

    def teamReports(self):
        if self.adapted.teamBasedEvaluation:
            if checkPermission('loops.ViewRestricted', self.context):
                return [dict(name='standard', label='label_survey_report_standard'),
                        dict(name='questions', 
                             label='label_survey_report_questions')]

    def update(self):
        instUid = self.request.form.get('select_institution')
        if instUid:
            return self.setInstitution(instUid)

    @Lazy
    def groups(self):
        result = []
        if self.questionnaireType == 'pref_selection':
            groups = [g.questions for g in 
                self.adapted.getQuestionGroups(self.personId)]
            questions = []
            for idxg, g in enumerate(groups):
                qus = []
                for idxq, qu in enumerate(g):
                    questions.append((idxg + 3 * idxq, idxg, qu))
            questions.sort()
            questions = [item[2] for item in questions]
            size = len(questions)
            for idx in range(0, size, 3):
                result.append(dict(title=u'Question', infoText=None, 
                                   questions=questions[idx:idx+3]))
            return [g for g in result if len(g['questions']) == 3]
        if self.adapted.noGrouping:
            questions = list(self.adapted.getQuestions(self.personId))
            questions.sort(key=lambda x: x.title)
            size = len(questions)
            bs = self.batchSize
            for idx in range(0, size, bs):
                result.append(dict(title=u'Question', infoText=None, 
                                   questions=questions[idx:idx+bs]))
        else:
            for group in self.adapted.getQuestionGroups(self.personId):
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
        if self.report == 'standard':
            cols = [c for c in cols if c['name'] in self.teamColumns]
        return cols

    teamColumns = ['category', 'average', 'stddev', 'teamRank', 'text']

    @Lazy
    def showTeamResults(self):
        for c in self.feedbackColumns:
            if c['name'] in ('average', 'teamRank'):
                return True
        return False

    def getTeamData(self, respManager):
        result = []
        pred = [self.conceptManager.get('ismember'),
                self.conceptManager.get('ismaster')]
        if None in pred:
            return result
        inst = self.institution
        instUid = self.getUidForObject(inst)
        if inst:
            for c in inst.getChildren(pred):
                uid = self.getUidForObject(c)
                data = respManager.load(uid, instUid)
                if data:
                    resp = Response(self.adapted, self.personId)
                    for qu in self.adapted.getQuestions(self.personId):
                        if qu.questionType in (None, 'value_selection'):
                            if qu.uid in data:
                                value = data[qu.uid]
                                if isinstance(value, int) or value.isdigit():
                                    resp.values[qu] = int(value)
                        else:
                            resp.texts[qu] = data.get(qu.uid) or u''
                    qgAvailable = True
                    for qg in self.adapted.getQuestionGroups(self.personId):
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
        if self.report:
            return self.teamResults(self.report)
        form = self.request.form
        action = None
        for k in ('submit', 'save'):
            if k in form:
                action = k
                break
        if action is None:
            return []
        respManager = Responses(self.context)
        respManager.personId = (self.request.form.get('person') or 
                                respManager.getPersonId())
        if self.adapted.teamBasedEvaluation and self.institution:
            respManager.institutionId = self.getUidForObject(
                                            baseObject(self.institution))
        if self.adapted.questionnaireType == 'person':
            respManager.referrerId = respManager.getPersonId()
        if self.adapted.questionnaireType == 'pref_selection':
            return self.prefsResults(respManager, form, action)
        data = {}
        response = Response(self.adapted, self.personId)
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
        self.data = data
        self.errors = self.check(response)
        if action == 'submit' and not self.errors:
            data['state'] = 'active'
        else:
            data['state'] = 'draft'
        respManager.save(data)
        if action == 'save':
            self.message = u'Your data have been saved.'
            return []
        if self.errors:
            return []
        result = [dict(category=r['group'].title, text=r['feedback'].text, 
                       score=int(round(r['score'] * 100)), rank=r['rank']) 
                    for r in values]
        if self.showTeamResults:
            self.teamData = self.getTeamData(respManager)
            groups = [r['group'] for r in values]
            teamValues = response.getTeamResult(groups, self.teamData)
            for idx, r in enumerate(teamValues):
                result[idx]['average'] = int(round(r['average'] * 100))
                result[idx]['teamRank'] = r['rank']
        return result

    def teamResults(self, report):
        result = []
        respManager = Responses(self.context)
        self.teamData = self.getTeamData(respManager)
        response = Response(self.adapted, None)
        groups = self.adapted.getQuestionGroups(self.personId)
        teamValues = response.getTeamResult(groups, self.teamData)
        for idx, r in enumerate(teamValues):
            group = r['group']
            item = dict(category=group.title,
                        average=int(round(r['average'] * 100)),
                        teamRank=r['rank'])
            if group.feedbackItems:
                wScore = r['average'] * len(group.feedbackItems) - 0.00001
                item['text'] = group.feedbackItems[int(wScore)].text
            result.append(item)
        return result

    def getTeamResultsForQuestion(self, question, questionnaire):
        result = dict(average=0.0, stddev=0.0)
        if self.teamData is None:
            respManager = Responses(self.context)
            self.teamData = self.getTeamData(respManager)
        answerRange = question.answerRange or questionnaire.defaultAnswerRange
        values = [r.values.get(question) for r in self.teamData]
        values = [v for v in values if v is not None]
        if values:
            average = float(sum(values)) / len(values)
            if question.revertAnswerOptions:
                average = answerRange - average - 1
            devs = [(average - v) for v in values]
            stddev = math.sqrt(sum(d * d for d in devs) / len(values))
            average = average * 100 / (answerRange - 1)
            stddev = stddev * 100 / (answerRange - 1)
            result['average'] = int(round(average))
            result['stddev'] = int(round(stddev))
        texts = [r.texts.get(question) for r in self.teamData]
        result['texts'] = '<br />'.join([unicode(t) for t in texts if t])
        return result

    def prefsResults(self, respManager, form, action):
        result = []
        data = {}
        for key, value in form.items():
            if key.startswith('group_') and value:
                data[value] = 1
        respManager.save(data)
        if action == 'save':
            self.message = u'Your data have been saved.'
            return []
        self.data = data
        #self.errors = self.check(response)
        if self.errors:
            return []
        for group in self.adapted.getQuestionGroups(self.personId):
            score = 0
            for qu in group.questions:
                value = data.get(qu.uid) or 0
                if qu.revertAnswerOptions:
                    value = -value
                score += value
            result.append(dict(category=group.title, score=score))
        return result

    def check(self, response):
        errors = []
        values = response.values
        for qu in self.adapted.getQuestions(self.personId):
            if qu.required and qu not in values:
                errors.append(dict(uid=qu.uid,
                    text='Please answer the obligatory questions.'))
                break
        qugroups = {}
        for qugroup in self.adapted.getQuestionGroups(self.personId):
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
            if self.adapted.teamBasedEvaluation and self.institution:
                respManager.institutionId = self.getUidForObject(
                                                baseObject(self.institution))
            if self.adapted.questionnaireType == 'person':
                respManager.referrerId = respManager.getPersonId()
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

    def getPrefsValue(self, question):
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

