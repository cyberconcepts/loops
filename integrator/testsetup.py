"""
Set up a loops site for testing.

$Id$
"""

from zope import component

from loops import util
from loops.concept import Concept
from loops.resource import Resource
from loops.integrator.interfaces import IExternalCollection
from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.tests.setup import TestSite as BaseTestSite


class TestSite(BaseTestSite):

    def __init__(self, site):
        self.site = site

    def setup(self):
        component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        concepts, resources, views = self.baseSetup()

        tType = concepts.getTypeConcept()

        tExtFile = concepts['extfile'] = Concept(u'External File')
        tExtCollection = concepts['extcollection'] = Concept(u'External Collection')

        self.indexAll(concepts, resources)
        return concepts, resources, views

