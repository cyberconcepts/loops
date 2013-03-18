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

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.knowledge.survey.questionnaire import Response
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops.organize.party import getPersonForUser


template = ViewPageTemplateFile('view_macros.pt')

class SurveyView(ConceptView):

    tabview = 'index.html'
    data = None

    @Lazy
    def macro(self):
        return template.macros['survey']

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
            # TODO: store self.data in track
        # else:
        #     get response from track
        if response is not None:
            result = response.getGroupedResult()
        return [dict(category=r[0].title, text=r[1].text, 
                            score=int(round(r[2] * 100)))
                        for r in result]

    def getValues(self, question):
        setting = None
        if self.data is not None:
            setting = self.data.get(question.uid)
        noAnswer = [dict(value='none', checked=(setting == None))]
        return noAnswer + [dict(value=i, checked=(setting == i)) 
                                for i in reversed(range(question.answerRange))]

