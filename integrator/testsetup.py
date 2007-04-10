"""
Set up a loops site for testing.

$Id$
"""

from zope import component
from zope.app.catalog.catalog import Catalog
from zope.app.catalog.interfaces import ICatalog
from zope.app.catalog.field import FieldIndex
from zope.app.catalog.text import TextIndex

from cybertools.relation.tests import IntIdsStub
from cybertools.relation.registry import RelationRegistry
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.relation.registry import IndexableRelationAdapter
from cybertools.typology.interfaces import IType

from loops import Loops
from loops import util
from loops.interfaces import IIndexAttributes
from loops.concept import Concept
from loops.concept import IndexAttributes as ConceptIndexAttributes
from loops.resource import Resource
from loops.resource import IndexAttributes as ResourceIndexAttributes
from loops.integrator.interfaces import IExternalCollection
from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.setup import SetupManager, addObject
from loops.tests.setup import TestSite as BaseTestSite
from loops.type import ConceptType, ResourceType, TypeConcept


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

