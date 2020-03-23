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
Surveys used in knowledge management.
"""

from zope.component import adapts
from zope.interface import implementer, implements

from cybertools.knowledge.survey.questionnaire import Questionnaire, \
            QuestionGroup, Question, FeedbackItem
from loops.common import adapted, AdapterBase
from loops.knowledge.survey.interfaces import IQuestionnaire, \
            IQuestionGroup, IQuestion, IFeedbackItem
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IQuestionnaire, 
            IQuestionGroup, IQuestion, IFeedbackItem)


class Questionnaire(AdapterBase, Questionnaire):

    implements(IQuestionnaire)

    _contextAttributes = list(IQuestionnaire)
    _adapterAttributes = AdapterBase._adapterAttributes + (
                'teamBasedEvaluation', 
                'questionGroups', 'questions', 'responses',)
    _noexportAttributes = _adapterAttributes

    def getTeamBasedEvaluation(self):
        return (self.questionnaireType == 'team' or
                    getattr(self.context, '_teamBasedEvaluation', False))
    def setTeamBasedEvaluation(self, value):
        if not value and getattr(self.context, '_teamBasedEvaluation', False):
            self.context._teamBasedEvaluation = False
    teamBasedEvaluation = property(getTeamBasedEvaluation, setTeamBasedEvaluation)

    @property
    def questionGroups(self):
        return self.getQuestionGroups()

    def getAllQuestionGroups(self, personId=None):
        return [adapted(c) for c in self.context.getChildren()]

    def getQuestionGroups(self, personId=None):
        return self.getAllQuestionGroups()

    @property
    def questions(self):
        return self.getQuestions()

    def getQuestions(self, personId=None):
        for qug in self.getQuestionGroups(personId):
            for qu in qug.questions:
                #qu.questionnaire = self
                yield qu


class QuestionGroup(AdapterBase, QuestionGroup):

    implements(IQuestionGroup)

    _contextAttributes = list(IQuestionGroup)
    _adapterAttributes = AdapterBase._adapterAttributes + (
                'questionnaire', 'questions', 'feedbackItems')
    _noexportAttributes = _adapterAttributes

    def getQuestionnaires(self):
        result = []
        for p in self.context.getParents():
            ap = adapted(p)
            if IQuestionnaire.providedBy(ap):
                result.append(ap)            
        return result

    @property
    def questionnaire(self):
        for qu in self.getQuestionnaires():
            return qu

    @property
    def subobjects(self):
        return [adapted(c) for c in self.context.getChildren()]

    @property
    def questions(self):
        return [obj for obj in self.subobjects if IQuestion.providedBy(obj)]

    @property
    def feedbackItems(self):
        return [obj for obj in self.subobjects if IFeedbackItem.providedBy(obj)]


class Question(AdapterBase, Question):

    implements(IQuestion)

    _contextAttributes = list(IQuestion)
    _adapterAttributes = AdapterBase._adapterAttributes + (
                'text', 'questionnaire', 'answerRange', 'feedbackItems',)
    _noexportAttributes = _adapterAttributes

    @property
    def text(self):
        return self.context.description

    @property
    def questionGroup(self):
        for p in self.context.getParents():
            ap = adapted(p)
            if IQuestionGroup.providedBy(ap):
                return ap

    @property
    def questionnaire(self):
        return self.questionGroup.questionnaire


class FeedbackItem(AdapterBase, FeedbackItem):

    implements(IFeedbackItem)

    _contextAttributes = list(IFeedbackItem)
    _adapterAttributes = AdapterBase._adapterAttributes + (
                'text',)
    _noexportAttributes = _adapterAttributes

    @property
    def text(self):
        return self.context.description
