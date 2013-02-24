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
Surveys used in knowledge management.
"""

from zope.component import adapts
from zope.interface import implementer, implements

from cybertools.knowledge.survey.questionnaire import Questionnaire, \
            QuestionGroup, Question, FeedbackItem
from loops.common import AdapterBase
from loops.knowledge.survey.interfaces import IQuestionnaire, \
            IQuestionGroup, IQuestion, IFeedbackItem
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IQuestionnaire, 
            IQuestionGroup, IQuestion, IFeedbackItem)


class Questionnaire(AdapterBase, Questionnaire):

    implements(IQuestionnaire)

    _contextAttributes = list(IQuestionnaire)


class QuestionGroup(AdapterBase, QuestionGroup):

    implements(IQuestionGroup)

    _contextAttributes = list(IQuestionGroup)


class Question(AdapterBase, Question):

    implements(IQuestion)

    _contextAttributes = list(IQuestion)


class FeedbackItem(AdapterBase, FeedbackItem):

    implements(IFeedbackItem)

    _contextAttributes = list(IFeedbackItem)

