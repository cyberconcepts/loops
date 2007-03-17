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
from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.setup import SetupManager, addObject
from loops.type import ConceptType, ResourceType, TypeConcept


class TestSite(object):

    def __init__(self, site):
        self.site = site

    def setup(self):
        site = self.site

        component.provideUtility(IntIdsStub())
        relations = RelationRegistry()
        relations.setupIndexes()
        component.provideUtility(relations, IRelationRegistry)
        component.provideAdapter(IndexableRelationAdapter)

        component.provideAdapter(ConceptType)
        component.provideAdapter(ResourceType)
        component.provideAdapter(TypeConcept)

        catalog = Catalog()
        component.provideUtility(catalog, ICatalog)

        catalog['loops_title'] = TextIndex('title', IIndexAttributes, True)
        catalog['loops_text'] = TextIndex('text', IIndexAttributes, True)
        catalog['loops_type'] = FieldIndex('tokenForSearch', IType, False)

        loopsRoot = site['loops'] = Loops()

        component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        setup = SetupManager(loopsRoot)
        concepts, resources, views = setup.setup()

        component.provideAdapter(ConceptIndexAttributes)
        component.provideAdapter(ResourceIndexAttributes)

        tType = concepts.getTypeConcept()
        tDomain = concepts['domain']
        tTextDocument = concepts['textdocument']

        tCountry = addObject(concepts, Concept, 'country', title=u'Country',
                           type=tType)
        tCustomer = addObject(concepts, Concept, 'customer', title=u'Customer',
                           type=tType)
        tState = addObject(concepts, Concept, 'state', title=u'State',
                            type=tType)
        tDocumentType = addObject(concepts, Concept, 'documenttype',
                           title=u'Document Type', type=tType)
        dGeneral = addObject(concepts, Concept, 'general',
                           title=u'General Domain', type=tDomain)
        dProjects = addObject(concepts, Concept, 'projects',
                           title=u'Project Domain', type=tDomain)
        tCountry.assignParent(dGeneral)
        tState.assignParent(dGeneral)
        tCustomer.assignParent(dProjects)
        tDocumentType.assignParent(dProjects)

        countryDe = addObject(concepts, Concept, 'country_de',
                           title=u'Germany', type=tCountry)
        countryUs = addObject(concepts, Concept, 'country_us',
                           title=u'USA', type=tCountry)
        cust1 = addObject(concepts, Concept, 'cust1',
                           title=u'Customer 1', type=tCustomer)
        cust2 = addObject(concepts, Concept, 'cust2',
                           title=u'Customer 2', type=tCustomer)
        cust3 = addObject(concepts, Concept, 'cust3',
                           title=u'Customer 3', type=tCustomer)
        cust1.assignParent(countryDe)
        cust2.assignParent(countryDe)
        cust3.assignParent(countryUs)
        stateNew = addObject(concepts, Concept, 'new',
                           title=u'New', type=tState)
        stateReleased = addObject(concepts, Concept, 'released',
                           title=u'Released', type=tState)
        stateObsolete = addObject(concepts, Concept, 'obsolete',
                           title=u'Obsolete', type=tState)
        dtStudy = addObject(concepts, Concept, 'dt_study',
                           title=u'Study', type=tDocumentType)
        dtNote = addObject(concepts, Concept, 'dt_note',
                           title=u'Note', type=tDocumentType)

        d001 = addObject(resources, Resource, 'd001',
                           title=u'Doc 001', type=tTextDocument)
        d001.assignConcept(cust1)
        d001.assignConcept(stateReleased)
        d001.assignConcept(dtNote)
        d002 = addObject(resources, Resource, 'd002',
                           title=u'Doc 002', type=tTextDocument)
        d002.assignConcept(cust3)
        d002.assignConcept(stateNew)
        d002.assignConcept(dtNote)
        d003 = addObject(resources, Resource, 'd003',
                           title=u'Doc 003', type=tTextDocument)
        d003.assignConcept(cust1)
        d003.assignConcept(stateNew)
        d003.assignConcept(dtStudy)

        for c in concepts.values():
             catalog.index_doc(int(util.getUidForObject(c)), c)
        for r in resources.values():
             catalog.index_doc(int(util.getUidForObject(r)), r)

        return concepts, resources, views


