# tests.py - loops.knowledge package

import os
import unittest, doctest
from zope.app.testing import ztapi
from zope import component
from zope.interface.verify import verifyClass
from zope.testing.doctestunit import DocFileSuite

from loops.knowledge.survey.base import Questionnaire, Question, ResultElement
from loops.knowledge.survey.interfaces import IQuestionnaire, IQuestion, \
                IResultElement
from loops.organize.party import Person
from loops.setup import importData as baseImportData


importPath = os.path.join(os.path.dirname(__file__), 'data')


def importData(loopsRoot):
    baseImportData(loopsRoot, importPath, 'knowledge_de.dmp')

def importSurvey(loopsRoot):
    component.provideAdapter(Questionnaire, provides=IQuestionnaire)
    component.provideAdapter(Question, provides=IQuestion)
    component.provideAdapter(ResultElement, provides=IResultElement)
    baseImportData(loopsRoot, importPath, 'survey_de.dmp')


class Test(unittest.TestCase):
    "Basic tests for the knowledge sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
