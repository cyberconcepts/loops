"""
Set up a loops site for testing.

$Id$
"""

from zope import component
from zope.annotation.attribute import AttributeAnnotations
from zope.app.catalog.catalog import Catalog
from zope.app.catalog.interfaces import ICatalog
from zope.app.catalog.field import FieldIndex
from zope.app.catalog.text import TextIndex
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.app.security.principalregistry import principalRegistry
from zope.app.security.interfaces import IAuthentication
from zope.app.session.interfaces import IClientIdManager, ISessionDataContainer
from zope.app.session import session
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import implements

from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.field import FieldInstance, NumberFieldInstance
from cybertools.composer.schema.instance import Instance, Editor
from cybertools.relation.tests import IntIdsStub
from cybertools.relation.registry import RelationRegistry
from cybertools.relation.interfaces import IRelation, IRelationRegistry
from cybertools.relation.interfaces import IRelationInvalidatedEvent
from cybertools.relation.registry import IndexableRelationAdapter
from cybertools.relation.registry import invalidateRelations, removeRelation
from cybertools.typology.interfaces import IType

from loops.base import Loops
from loops import util
from loops.common import NameChooser
from loops.interfaces import ILoopsObject, IIndexAttributes
from loops.interfaces import IDocument, IFile, ITextDocument
from loops.concept import Concept
from loops.concept import IndexAttributes as ConceptIndexAttributes
from loops.query import QueryConcept
from loops.resource import Resource, FileAdapter, TextDocumentAdapter
from loops.resource import IndexAttributes as ResourceIndexAttributes
from loops.schema import ResourceSchemaFactory, FileSchemaFactory, NoteSchemaFactory
from loops.setup import SetupManager, addObject
from loops.type import LoopsType, ConceptType, ResourceType, TypeConcept
from loops.view import NodeAdapter


class ClientIdManager(object):
    """ dummy, for testing only """
    implements(IClientIdManager)
    def getClientId(self, request):
        return 'dummy'


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

        component.provideAdapter(ZDCAnnotatableAdapter, (ILoopsObject,), IZopeDublinCore)
        component.provideAdapter(AttributeAnnotations, (ILoopsObject,))
        component.provideUtility(principalRegistry, IAuthentication)
        component.provideAdapter(session.ClientId)
        component.provideAdapter(session.Session)
        component.provideUtility(session.RAMSessionDataContainer(), ISessionDataContainer)
        component.provideUtility(ClientIdManager())

        component.provideAdapter(LoopsType)
        component.provideAdapter(ConceptType)
        component.provideAdapter(ResourceType, (IDocument,))
        component.provideAdapter(TypeConcept)
        component.provideAdapter(QueryConcept)
        component.provideAdapter(FileAdapter, provides=IFile)
        component.provideAdapter(TextDocumentAdapter, provides=ITextDocument)
        component.provideAdapter(NodeAdapter)
        component.provideAdapter(NameChooser)
        component.provideAdapter(Instance)
        component.provideAdapter(Editor, name='editor')
        component.provideAdapter(FieldInstance)
        component.provideAdapter(NumberFieldInstance, name='number')

        component.provideAdapter(SchemaFactory)
        component.provideAdapter(ResourceSchemaFactory)
        component.provideAdapter(FileSchemaFactory)
        component.provideAdapter(NoteSchemaFactory)

        component.getSiteManager().registerHandler(invalidateRelations,
                            (ILoopsObject, IObjectRemovedEvent))
        component.getSiteManager().registerHandler(removeRelation,
                            (IRelation, IRelationInvalidatedEvent))

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

