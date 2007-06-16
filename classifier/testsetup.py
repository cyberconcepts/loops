"""
Set up a loops site for testing.

$Id$
"""

import os
from zope import component

from loops import util
from loops.interfaces import IFile, IExternalFile
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

        self.indexAll(concepts, resources)
        return concepts, resources, views

