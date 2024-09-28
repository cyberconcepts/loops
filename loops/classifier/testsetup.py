# loops.classifier.testsetup
"""
Set up a loops site for testing.
"""

import os
from zope import component
#from zope.catalog.interfaces import ICatalog
#from zope.catalog.text import TextIndex

from cybertools.storage.interfaces import IExternalStorage
from cybertools.storage.filesystem import fullPathStorage
from loops import util
from loops.classifier.base import Classifier
from loops.classifier.sample import SampleAnalyzer
from loops.classifier.standard import FilenameExtractor
from loops.classifier.interfaces import IClassifier, IAnalyzer
from loops.common import adapted
from loops.concept import Concept
from loops.resource import Resource, ExternalFileAdapter
from loops.interfaces import IConcept, IIndexAttributes, IExternalFile
from loops.integrator.collection import DirectoryCollectionProvider
from loops.integrator.collection import ExternalCollectionAdapter
from loops.integrator.interfaces import IExternalCollection, IExternalCollectionProvider
from loops.organize.setup import SetupManager as OrganizeSetupManager
#from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.knowledge.knowledge import Person
from loops.knowledge.interfaces import IPerson
from loops.setup import SetupManager, addAndConfigureObject
from loops.tests.setup import TestSite as BaseTestSite

dataDir = os.path.join(os.path.dirname(__file__), 'testdata')


class TestSite(BaseTestSite):

    def __init__(self, site):
        self.site = site

    def setup(self):
        #component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        component.provideAdapter(OrganizeSetupManager, name='organize')
        concepts, resources, views = self.baseSetup()

        # classifier and Co
        tType = concepts.getTypeConcept()
        tClassifier = addAndConfigureObject(concepts, Concept, 'classifier',
                                title=u'Classifier', conceptType=tType,
                                typeInterface=IClassifier)
        component.provideAdapter(Classifier)
        sampleClassifier = addAndConfigureObject(concepts, Concept,
                                'fileclassifier', title=u'File Classifier',
                                conceptType=tClassifier)
        sampleClassifier = adapted(sampleClassifier)
        sampleClassifier.extractors = 'filename'
        sampleClassifier.analyzer = 'sample'
        component.provideAdapter(FilenameExtractor, name='filename')
        component.provideAdapter(SampleAnalyzer, name='sample')

        # external file stuff for providing test files
        component.provideAdapter(ExternalFileAdapter, provides=IExternalFile)
        component.provideUtility(fullPathStorage(), IExternalStorage, name='fullpath')
        component.provideAdapter(ExternalCollectionAdapter)
        component.provideUtility(DirectoryCollectionProvider(), IExternalCollectionProvider)
        tExtFile = addAndConfigureObject(concepts, Concept, 'extfile',
                                title=u'External File', conceptType=tType,
                                typeInterface=IExternalFile)
        tExtCollection = addAndConfigureObject(concepts, Concept, 'extcollection',
                                title=u'External Collection', conceptType=tType,
                                typeInterface=IExternalCollection)

        component.provideAdapter(Person, (IConcept,), IPerson)

        self.indexAll(concepts, resources)
        return concepts, resources, views

