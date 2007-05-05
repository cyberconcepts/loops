"""
Set up a loops site for testing.

$Id$
"""

import os
from zope import component

from cybertools.storage.interfaces import IExternalStorage
from cybertools.storage.filesystem import fullPathStorage
from loops import util
from loops.interfaces import IFile, IExternalFile
from loops.concept import Concept
from loops.resource import Resource, FileAdapter, ExternalFileAdapter
from loops.integrator.interfaces import IExternalCollection
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

        component.provideAdapter(FileAdapter, provides=IFile)
        component.provideAdapter(ExternalFileAdapter, provides=IExternalFile)

        component.provideUtility(fullPathStorage(), IExternalStorage, name='fullpath')

        tType = concepts.getTypeConcept()
        tExtFile = addAndConfigureObject(concepts, Concept, 'extfile',
                                title=u'External File', conceptType=tType,
                                typeInterface=IExternalFile)
        tExtCollection = addAndConfigureObject(concepts, Concept, 'extcollection',
                                title=u'External Collection', conceptType=tType,
                                typeInterface=IExternalCollection)

        self.indexAll(concepts, resources)
        return concepts, resources, views

