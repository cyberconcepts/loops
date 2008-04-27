"""
Set up a loops site for testing.

$Id$
"""

from zope import component
from zope.app.catalog.interfaces import ICatalog

from cybertools.typology.interfaces import IType
from loops import util
from loops.concept import Concept
from loops.resource import Resource
from loops.knowledge.interfaces import IPerson
from loops.knowledge.knowledge import Person
from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.setup import SetupManager, addObject
from loops.tests.setup import TestSite as BaseTestSite
from loops.type import ConceptType, ResourceType, TypeConcept


class TestSite(BaseTestSite):

    def __init__(self, site):
        self.site = site

    def setup(self):
        super(TestSite, self).setup()
        site = self.site
        loopsRoot = site['loops']

        component.provideAdapter(Person, provides=IPerson)

        component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        setup = SetupManager(loopsRoot)
        concepts, resources, views = setup.setup()

        tType = concepts.getTypeConcept()
        tDomain = concepts['domain']
        tTextDocument = concepts['textdocument']
        tPerson = concepts['person']

        tCountry = addObject(concepts, Concept, 'country', title=u'Country',
                           type=tType)
        tCustomer = addObject(concepts, Concept, 'customer', title=u'Customer',
                           type=tType)
        tDocumentType = addObject(concepts, Concept, 'documenttype',
                           title=u'Document Type', type=tType)
        dGeneral = addObject(concepts, Concept, 'general',
                           title=u'General Domain', type=tDomain)
        dProjects = addObject(concepts, Concept, 'projects',
                           title=u'Project Domain', type=tDomain)
        tCountry.assignParent(dGeneral)
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
        dtStudy = addObject(concepts, Concept, 'dt_study',
                           title=u'Study', type=tDocumentType)
        dtNote = addObject(concepts, Concept, 'dt_note',
                           title=u'Note', type=tDocumentType)

        jim = addObject(concepts, Concept, 'jim', title=u'Jim', type=tPerson)
        jim.assignChild(cust1)

        d001 = resources['d001.txt']
        d001.assignConcept(cust1)
        d001.assignConcept(dtNote)
        d002 = resources['d002.txt']
        d002.assignConcept(cust3)
        d002.assignConcept(dtNote)
        d003 = resources['d003.txt']
        d003.assignConcept(cust1)
        d003.assignConcept(dtStudy)

        catalog = component.getUtility(ICatalog)
        for c in concepts.values():
             catalog.index_doc(int(util.getUidForObject(c)), c)
        for r in resources.values():
             catalog.index_doc(int(util.getUidForObject(r)), r)

        return concepts, resources, views

