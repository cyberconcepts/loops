"""
Set up a loops site for testing.

$Id$
"""

import os
from zope import component

from loops import util
from loops.classifier.base import Classifier, Extractor, Analyzer
from loops.classifier.interfaces import IClassifier, IAnalyzer
from loops.concept import Concept
from loops.resource import Resource
from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.setup import SetupManager, addAndConfigureObject
from loops.tests.setup import TestSite as BaseTestSite

dataDir = os.path.join(os.path.dirname(__file__), 'testdata')


class TestSite(BaseTestSite):

    def __init__(self, site):
        self.site = site

    def setup(self):
        component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        concepts, resources, views = self.baseSetup()

        tType = concepts.getTypeConcept()
        tClassifier = addAndConfigureObject(concepts, Concept, 'classifier',
                                title=u'Classifier', conceptType=tType,
                                typeInterface=IClassifier)

        component.provideAdapter(Classifier)
        fileClassifier = addAndConfigureObject(concepts, Concept,
                                'fileclassifier', title=u'File Classifier',
                                conceptType=tClassifier)

        component.provideAdapter(Extractor)
        component.provideUtility(Analyzer, IAnalyzer)

        self.indexAll(concepts, resources)
        return concepts, resources, views

