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
from loops.common import NameChooser
from loops.interfaces import IIndexAttributes, IDocument
from loops.concept import Concept
from loops.concept import IndexAttributes as ConceptIndexAttributes
from loops.resource import Resource
from loops.resource import IndexAttributes as ResourceIndexAttributes
from loops.setup import SetupManager, addObject
from loops.type import LoopsType, ConceptType, ResourceType, TypeConcept


class TestSite(object):

    def __init__(self, site):
        self.site = site

    def baseSetup(self):
        site = self.site

        component.provideUtility(IntIdsStub())
        relations = RelationRegistry()
        relations.setupIndexes()
        component.provideUtility(relations, IRelationRegistry)
        component.provideAdapter(IndexableRelationAdapter)

        component.provideAdapter(LoopsType)
        component.provideAdapter(ConceptType)
        component.provideAdapter(ResourceType, (IDocument,))
        component.provideAdapter(TypeConcept)
        component.provideAdapter(NameChooser)

        catalog = self.catalog = Catalog()
        component.provideUtility(catalog, ICatalog)
        catalog['loops_title'] = TextIndex('title', IIndexAttributes, True)
        catalog['loops_text'] = TextIndex('text', IIndexAttributes, True)
        catalog['loops_type'] = FieldIndex('tokenForSearch', IType, False)
        component.provideAdapter(ConceptIndexAttributes)
        component.provideAdapter(ResourceIndexAttributes)

        loopsRoot = site['loops'] = Loops()
        setup = SetupManager(loopsRoot)
        concepts, resources, views = setup.setup()
        return concepts, resources, views

    def setup(self):
        concepts, resources, views = self.baseSetup()
        catalog = component.getUtility(ICatalog)

        tType = concepts.getTypeConcept()
        tDomain = concepts['domain']
        tTextDocument = concepts['textdocument']
        tFile = concepts['file']

        tCustomer = addObject(concepts, Concept, 'customer', title=u'Customer',
                           conceptType=tType)
        dProjects = addObject(concepts, Concept, 'projects',
                           title=u'Project Domain', conceptType=tDomain)
        tCustomer.assignParent(dProjects)

        d001 = addObject(resources, Resource, 'd001.txt',
                           title=u'Doc 001', resourceType=tTextDocument)
        d002 = addObject(resources, Resource, 'd002.txt',
                           title=u'Doc 002', resourceType=tTextDocument)
        d003 = addObject(resources, Resource, 'd003.txt',
                           title=u'Doc 003', resourceType=tTextDocument)

        self.indexAll(concepts, resources)
        return concepts, resources, views

    def indexAll(self, concepts, resources):
        for c in concepts.values():
             self.catalog.index_doc(int(util.getUidForObject(c)), c)
        for r in resources.values():
             self.catalog.index_doc(int(util.getUidForObject(r)), r)

