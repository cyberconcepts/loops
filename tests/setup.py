"""
Set up a loops site for testing.

$Id$
"""

from zope import component
from zope.annotation.attribute import AttributeAnnotations
from zope.annotation.interfaces import IAnnotatable
from zope.app.catalog.catalog import Catalog
from zope.app.catalog.interfaces import ICatalog
from zope.app.catalog.field import FieldIndex
from zope.app.catalog.text import TextIndex
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.app.principalannotation import PrincipalAnnotationUtility
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.renderer.rest import IReStructuredTextSource,\
                ReStructuredTextToHTMLRenderer, ReStructuredTextSourceFactory
from zope.app.security.principalregistry import principalRegistry
from zope.app.security.interfaces import IAuthentication
from zope.app.session.interfaces import IClientIdManager, ISessionDataContainer
from zope.app.session import session
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import Interface, implements
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserView
from zope.security.checker import Checker, defineChecker
from zope.security.management import setSecurityPolicy
from zope.securitypolicy.zopepolicy import ZopeSecurityPolicy
from zope.securitypolicy.principalrole import AnnotationPrincipalRoleManager
from zope.securitypolicy.rolepermission import AnnotationRolePermissionManager

from cybertools.browser.controller import Controller
from cybertools.catalog.keyword import KeywordIndex
from cybertools.composer.schema.factory import SchemaFactory
from cybertools.composer.schema.field import FieldInstance, NumberFieldInstance
from cybertools.composer.schema.field import DateFieldInstance, BooleanFieldInstance
from cybertools.composer.schema.field import EmailFieldInstance, ListFieldInstance
from cybertools.composer.schema.field import FileUploadFieldInstance
from cybertools.composer.schema.grid.field import RecordsFieldInstance
from cybertools.composer.schema.instance import Instance, Editor
from cybertools.relation.tests import IntIdsStub
from cybertools.relation.registry import RelationRegistry, IIndexableRelation
from cybertools.relation.interfaces import IRelation, IRelationRegistry
from cybertools.relation.interfaces import IRelationInvalidatedEvent
from cybertools.relation.registry import IndexableRelationAdapter
from cybertools.relation.registry import invalidateRelations, removeRelation
from cybertools.stateful.interfaces import IStatefulIndexInfo
from cybertools.text.html import HtmlTransform
from cybertools.typology.interfaces import IType
from cybertools.wiki.base.config import WikiConfiguration
from cybertools.wiki.dcu.html import Writer as DocutilsHTMLWriter
from cybertools.wiki.dcu import process
from cybertools.wiki.dcu.rstx import Parser as DocutilsRstxParser
#from cybertools.wiki.tracking.link import LinkManager

from loops.base import Loops
from loops import util
from loops.browser.node import ViewPropertiesConfigurator
from loops.common import NameChooser
from loops.concept import Concept
from loops.concept import IndexAttributes as ConceptIndexAttributes
from loops.config.base import GlobalOptions, LoopsOptions
from loops.config.base import QueryOptions, PredicateOptions, TypeOptions
from loops.interfaces import ILoopsObject, IIndexAttributes
from loops.interfaces import IDocument, IFile, ITextDocument
from loops.layout.base import LayoutNode
from loops.organize.memberinfo import MemberInfoProvider
from loops.organize.stateful.base import StatefulResourceIndexInfo, handleTransition
from loops.predicate import Predicate   #, MappingAttributeRelation
from loops.expert.concept import QueryConcept
from loops.resource import Resource, FileAdapter, TextDocumentAdapter
from loops.resource import Document, MediaAsset
from loops.resource import IndexAttributes as ResourceIndexAttributes
from loops.schema.factory import ResourceSchemaFactory, FileSchemaFactory, \
                                 NoteSchemaFactory
from loops.schema.field import RelationFieldInstance, RelationSetFieldInstance
from loops.security.common import grantAcquiredSecurity, revokeAcquiredSecurity
from loops.security.policy import LoopsSecurityPolicy
from loops.security.setter import BaseSecuritySetter
from loops.security.setter import ConceptSecuritySetter, ResourceSecuritySetter
from loops.setup import SetupManager, addObject
from loops.table import DataTable
from loops.type import LoopsType, ConceptType, ResourceType, TypeConcept
from loops.versioning.versionable import VersionableResource
from loops.view import Node, NodeAdapter
#from loops.wiki.link import LoopsLinkProcessor
from loops.wiki.setup import SetupManager as WikiSetupManager


class ClientIdManager(object):
    """ dummy, for testing only """
    implements(IClientIdManager)
    def getClientId(self, request):
        return 'dummy'


class TestSite(object):

    def __init__(self, site):
        self.site = site

    def baseSetup(self):
        #oldPolicy = setSecurityPolicy(ZopeSecurityPolicy)
        oldPolicy = setSecurityPolicy(LoopsSecurityPolicy)
        checker = Checker(dict(title='zope.View', data='zope.View', body='zope.View'),
                          dict(title='zope.ManageContent'))
        defineChecker(Concept, checker)
        defineChecker(Resource, checker)
        defineChecker(Document, checker)
        defineChecker(Node, checker)

        component.provideUtility(IntIdsStub())
        relations = RelationRegistry()
        relations.setupIndexes()
        component.provideUtility(relations, IRelationRegistry)

        component.provideUtility(PrincipalAnnotationUtility(), IPrincipalAnnotationUtility)
        component.provideAdapter(IndexableRelationAdapter)
        component.provideAdapter(ZDCAnnotatableAdapter, (ILoopsObject,), IZopeDublinCore)
        component.provideAdapter(AttributeAnnotations, (ILoopsObject,))
        component.provideAdapter(AnnotationPrincipalRoleManager, (ILoopsObject,))
        component.provideAdapter(AnnotationRolePermissionManager, (ILoopsObject,))
        component.provideUtility(principalRegistry, IAuthentication)
        component.provideAdapter(session.ClientId)
        component.provideAdapter(session.Session)
        component.provideUtility(session.RAMSessionDataContainer(),
                                 ISessionDataContainer)
        component.provideUtility(ClientIdManager())
        component.provideUtility(ReStructuredTextSourceFactory,
                                 name='zope.source.rest')
        component.provideAdapter(ReStructuredTextToHTMLRenderer,
                                 (IReStructuredTextSource, IBrowserRequest), Interface)

        component.provideAdapter(LoopsType)
        component.provideAdapter(ConceptType)
        component.provideAdapter(Predicate)
        #component.provideAdapter(MappingAttributeRelation)
        component.provideAdapter(ResourceType, (IDocument,))
        component.provideAdapter(TypeConcept)
        component.provideAdapter(QueryConcept)
        component.provideAdapter(DataTable)
        component.provideAdapter(FileAdapter, provides=IFile)
        component.provideAdapter(TextDocumentAdapter, provides=ITextDocument)
        component.provideAdapter(NodeAdapter)
        component.provideAdapter(ViewPropertiesConfigurator)
        component.provideAdapter(NameChooser)
        component.provideHandler(grantAcquiredSecurity)
        component.provideHandler(revokeAcquiredSecurity)
        component.provideAdapter(BaseSecuritySetter)
        component.provideAdapter(ConceptSecuritySetter)
        component.provideAdapter(ResourceSecuritySetter)
        component.provideAdapter(LoopsOptions)
        component.provideAdapter(PredicateOptions)
        component.provideAdapter(QueryOptions)
        component.provideAdapter(TypeOptions)
        component.provideUtility(GlobalOptions())
        component.provideAdapter(VersionableResource)

        component.provideAdapter(Instance)
        component.provideAdapter(Editor, name='editor')
        component.provideAdapter(FieldInstance)
        component.provideAdapter(NumberFieldInstance, name='number')
        component.provideAdapter(DateFieldInstance, name='date')
        component.provideAdapter(EmailFieldInstance, name='email')
        component.provideAdapter(BooleanFieldInstance, name='boolean')
        component.provideAdapter(ListFieldInstance, name='list')
        component.provideAdapter(FileUploadFieldInstance, name='fileupload')
        component.provideAdapter(RecordsFieldInstance, name='records')
        component.provideAdapter(RelationFieldInstance, name='relation')
        component.provideAdapter(RelationSetFieldInstance, name='relationset')
        component.provideAdapter(SchemaFactory)
        component.provideAdapter(ResourceSchemaFactory)
        component.provideAdapter(FileSchemaFactory)
        component.provideAdapter(NoteSchemaFactory)

        component.provideAdapter(Controller, (Interface, IBrowserRequest),
                                 IBrowserView, name='controller')
        component.provideAdapter(MemberInfoProvider,
                                 (ILoopsObject, IBrowserRequest))

        component.getSiteManager().registerHandler(invalidateRelations,
                            (ILoopsObject, IObjectRemovedEvent))
        component.getSiteManager().registerHandler(removeRelation,
                            (IRelation, IRelationInvalidatedEvent))

        catalog = self.catalog = Catalog()
        component.provideUtility(catalog, ICatalog)
        catalog['loops_title'] = TextIndex('title', IIndexAttributes, True)
        catalog['loops_text'] = TextIndex('text', IIndexAttributes, True)
        catalog['loops_identifier'] = FieldIndex('identifier', IIndexAttributes, True)
        catalog['loops_type'] = FieldIndex('tokenForSearch', IType, False)
        catalog['loops_keywords'] = KeywordIndex('keywords', IIndexAttributes, True)
        catalog['loops_state'] = KeywordIndex('tokens', IStatefulIndexInfo, False)
        component.provideAdapter(ConceptIndexAttributes)
        component.provideAdapter(ResourceIndexAttributes)
        component.provideAdapter(HtmlTransform, (ITextDocument,), name='text/html')
        component.provideAdapter(StatefulResourceIndexInfo)
        component.provideHandler(handleTransition)

        component.provideAdapter(WikiSetupManager, name='wiki')
        component.provideUtility(WikiConfiguration())
        #component.provideAdapter(LinkManager)
        component.provideUtility(DocutilsHTMLWriter(), name='docutils.html')
        component.provideUtility(DocutilsRstxParser(), name='docutils.rstx')
        #component.provideAdapter(LoopsLinkProcessor, name='loops')
        component.provideAdapter(process.Reference, name='default')

        loopsRoot = self.site['loops'] = Loops()
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

        home = addObject(views, Node, 'home', title=u'Home', nodeType=u'menu')

        self.indexAll(concepts, resources)
        return concepts, resources, views

    def siteSetup(self, rootName='loops'):
        loopsRoot = self.site[rootName] = Loops()
        setup = SetupManager(loopsRoot)
        return setup.setup()

    def indexAll(self, concepts, resources):
        for c in concepts.values():
             self.catalog.index_doc(int(util.getUidForObject(c)), c)
        for r in resources.values():
             self.catalog.index_doc(int(util.getUidForObject(r)), r)

