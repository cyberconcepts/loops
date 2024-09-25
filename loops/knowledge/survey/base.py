# loops.knowledge.survey.base

""" Surveys used in knowledge management.
"""

from zope.component import adapts
from zope.interface import implementer

from cybertools.knowledge.survey.questionnaire import Questionnaire, \
            QuestionGroup, Question, FeedbackItem
from loops.common import adapted, AdapterBase
from loops.knowledge.survey.interfaces import IQuestionnaire, \
            IQuestionGroup, IQuestion, IFeedbackItem
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IQuestionnaire, 
            IQuestionGroup, IQuestion, IFeedbackItem)


@implementer(IQuestionnaire)
class Questionnaire(AdapterBase, Questionnaire):

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


@implementer(IQuestionGroup)
class QuestionGroup(AdapterBase, QuestionGroup):

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


@implementer(IQuestion)
class Question(AdapterBase, Question):

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


@implementer(IFeedbackItem)
class FeedbackItem(AdapterBase, FeedbackItem):

    _contextAttributes = list(IFeedbackItem)
    _adapterAttributes = AdapterBase._adapterAttributes + (
                'text',)
    _noexportAttributes = _adapterAttributes

    @property
    def text(self):
        return self.context.description
