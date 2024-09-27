# loops.versioning.testsetup

""" Set up a loops site for testing.
"""

from zope import component
from zope.annotation.attribute import AttributeAnnotations
from zope.annotation.interfaces import IAnnotatable
from zope.authentication.interfaces import IAuthentication
from zope.catalog.catalog import Catalog
from zope.catalog.interfaces import ICatalog
from zope.catalog.field import FieldIndex
from zope.catalog.text import TextIndex
from zope.container.interfaces import IObjectRemovedEvent
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.interfaces import IZopeDublinCore
from zope.principalregistry.principalregistry import principalRegistry

from cybertools.meta.interfaces import IOptions
from cybertools.relation.tests import IntIdsStub
from cybertools.relation.registry import RelationRegistry
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.relation.registry import IndexableRelationAdapter
from cybertools.typology.interfaces import IType

from loops.base import Loops
from loops import util
from loops.interfaces import IResource, IIndexAttributes
from loops.common import LoopsDCAdapter
from loops.concept import Concept
from loops.concept import IndexAttributes as ConceptIndexAttributes
from loops.config.base import LoopsOptions
from loops.interfaces import ILoopsObject, IConcept
from loops.resource import Resource
from loops.resource import IndexAttributes as ResourceIndexAttributes
#from loops.knowledge.setup import SetupManager as KnowledgeSetupManager
from loops.setup import SetupManager, addObject
from loops.type import ConceptType, ResourceType, TypeConcept
from loops.versioning.versionable import cleanupVersions


class TestSite(object):

    def __init__(self, site):
        self.site = site

    def setup(self):
        site = self.site

        component.provideUtility(IntIdsStub())
        relations = RelationRegistry()
        relations.setupIndexes()
        component.provideUtility(relations, IRelationRegistry)
        component.provideUtility(principalRegistry, IAuthentication)
        component.provideAdapter(IndexableRelationAdapter)
        component.provideAdapter(ZDCAnnotatableAdapter, (ILoopsObject,), IZopeDublinCore)
        component.provideAdapter(AttributeAnnotations, (ILoopsObject,))
        component.provideAdapter(LoopsDCAdapter, (IConcept,), IZopeDublinCore)
        component.provideAdapter(LoopsOptions, provides=IOptions)

        component.provideAdapter(ConceptType)
        component.provideAdapter(ResourceType)
        component.provideAdapter(TypeConcept)

        catalog = Catalog()
        component.provideUtility(catalog, ICatalog)

        catalog['loops_title'] = TextIndex('title', IIndexAttributes, True)
        catalog['loops_text'] = TextIndex('text', IIndexAttributes, True)
        catalog['loops_type'] = FieldIndex('tokenForSearch', IType, False)

        component.getSiteManager().registerHandler(cleanupVersions,
                            (IResource, IObjectRemovedEvent))

        loopsRoot = site['loops'] = Loops()

        #component.provideAdapter(KnowledgeSetupManager, name='knowledge')
        setup = SetupManager(loopsRoot)
        concepts, resources, views = setup.setup()

        component.provideAdapter(ConceptIndexAttributes)
        component.provideAdapter(ResourceIndexAttributes)

        tType = concepts.getTypeConcept()
        tDomain = concepts['domain']
        tTextDocument = concepts['textdocument']

        tCustomer = addObject(concepts, Concept, 'customer', title=u'Customer',
                           conceptType=tType)
        dProjects = addObject(concepts, Concept, 'projects',
                           title=u'Project Domain', conceptType=tDomain)
        tCustomer.assignParent(dProjects)

        cust1 = addObject(concepts, Concept, 'cust1',
                           title=u'Customer 1', conceptType=tCustomer)
        cust2 = addObject(concepts, Concept, 'cust2',
                           title=u'Customer 2', conceptType=tCustomer)
        cust3 = addObject(concepts, Concept, 'cust3',
                           title=u'Customer 3', conceptType=tCustomer)
        d001 = addObject(resources, Resource, 'd001.txt',
                           title=u'Doc 001', resouceType=tTextDocument)
        d001.assignConcept(cust1)
        d002 = addObject(resources, Resource, 'd002.txt',
                           title=u'Doc 002', resouceType=tTextDocument)
        d002.assignConcept(cust3)
        d003 = addObject(resources, Resource, 'd003.txt',
                           title=u'Doc 003', resouceType=tTextDocument)
        d003.assignConcept(cust1)

        for c in concepts.values():
             catalog.index_doc(int(util.getUidForObject(c)), c)
        for r in resources.values():
             catalog.index_doc(int(util.getUidForObject(r)), r)

        return concepts, resources, views


