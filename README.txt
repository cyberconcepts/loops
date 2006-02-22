===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  
  >>> from zope.app import zapi
  >>> from zope.app.tests import ztapi
  >>> from zope.interface import Interface
  >>> from zope.publisher.browser import TestRequest
  

Concepts and Relations
======================

Let's start with creating a few example concepts, putting them in a
top-level loops container and a concept manager:

  >>> from loops import Loops
  >>> site['loops'] = Loops()
  >>> loopsRoot = site['loops']

  >>> from loops.concept import ConceptManager, Concept
  >>> loopsRoot['concepts'] = ConceptManager()
  >>> concepts = loopsRoot['concepts']
  >>> cc1 = Concept()
  >>> concepts['cc1'] = cc1
  >>> cc1.title
  u''
  >>> loopsRoot.getLoopsUri(cc1)
  '.loops/concepts/cc1'

  >>> cc2 = Concept(u'Zope 3')
  >>> concepts['cc2'] = cc2
  >>> cc2.title
  u'Zope 3'

Now we want to relate the second concept to the first one.

In order to do this we first have to provide a relation registry. For
testing we use a simple dummy implementation. As relationships are
based on predicates that are themselves concepts we also need a
default predicate concept; the default name for this is 'standard'.

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> from zope.app.testing import ztapi
  >>> ztapi.provideUtility(IRelationRegistry, DummyRelationRegistry())
  >>> concepts['standard'] = Concept(u'subconcept')

Now we can assign the concept c2 as a child to c1 (using the standard
ConceptRelation):
        
  >>> cc1.assignChild(cc2)

We can now ask our concepts for their related child and parent concepts:

  >>> [zapi.getName(c) for c in cc1.getChildren()]
  [u'cc2']
  >>> len(cc1.getParents())
  0
  >>> [zapi.getName(p) for p in cc2.getParents()]
  [u'cc1']

  >>> len(cc2.getChildren())
  0

Each concept should have a concept type; this is in fact provided by a
relation to a special kind of concept object with the magic name 'type'.
This type object is its own type. The type relations themselves are of
a special predicate 'hasType'.

  >>> concepts['hasType'] = Concept(u'has type')
  >>> concepts['type'] = Concept(u'Type')
  >>> typeObject = concepts['type']
  >>> typeObject.setConceptType(typeObject)
  >>> typeObject.getConceptType().title
  u'Type'

  >>> concepts['unknown'] = Concept(u'Unknown Type')
  >>> unknown = concepts['unknown']
  >>> unknown.setConceptType(typeObject)
  >>> unknown.getConceptType().title
  u'Type'

  >>> cc1.setConceptType(unknown)
  >>> cc1.getConceptType().title
  u'Unknown Type'

  >>> concepts['topic'] = Concept(u'Topic')
  >>> topic = concepts['topic']
  >>> topic.setConceptType(typeObject)
  >>> cc1.setConceptType(topic)
  >>> cc1.getConceptType().title
  u'Topic'

We get a list of types using the ConceptTypeSourceList:

  >>> from loops.concept import ConceptTypeSourceList
  >>> types = ConceptTypeSourceList(cc1)
  >>> sorted(t.title for t in types)
  [u'Topic', u'Type', u'Unknown Type']

Using a PredicateSourceList we can retrieve a list of the available
predicates. In order for this to work we first have to assign our predicates
a special concept type.

  >>> concepts['predicate'] = Concept(u'Predicate')
  >>> predicate = concepts['predicate']
  >>> concepts['hasType'].conceptType = predicate
  >>> concepts['standard'].conceptType = predicate

  >>> from loops.concept import PredicateSourceList
  >>> predicates = PredicateSourceList(cc1)
  >>> sorted(t.title for t in predicates)
  [u'has type', u'subconcept']

Concept Views
-------------

  >>> from loops.browser.concept import ConceptView
  >>> view = ConceptView(cc1, TestRequest())

  >>> children = list(view.children())
  >>> [c.title for c in children]
  [u'Zope 3']

The token attribute provided with the items returned by the children() and
parents() methods identifies identifies not only the item itself but
also the relationship to the context object using a combination
of URIs to item and the predicate of the relationship:
  
  >>> [c.token for c in children]
  ['.loops/concepts/cc2:.loops/concepts/standard']

The concept view allows updating the underlying context object:

  >>> cc3 = Concept(u'loops for Zope 3')
  >>> concepts['cc3'] = cc3
  >>> view = ConceptView(cc1,
  ...           TestRequest(action='assign', tokens=['.loops/concepts/cc3']))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  [u'Zope 3', u'loops for Zope 3']

  >>> view = ConceptView(cc1,
  ...           TestRequest(action='remove', qualifier='children',
  ...               tokens=['.loops/concepts/cc2:.loops/concepts/standard']))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  [u'loops for Zope 3']

We can also create a new concept and assign it:

  >>> params = {'action': 'create', 'create.name': 'cc4',
  ...           'create.title': u'New concept'}
  >>> view = ConceptView(cc1, TestRequest(**params))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  [u'New concept', u'loops for Zope 3']

The concept view provides methods for displaying concept types and
predicates:

  >>> from zope.publisher.interfaces.browser import IBrowserRequest
  >>> from loops.browser.common import LoopsTerms
  >>> from zope.app.form.browser.interfaces import ITerms
  >>> from zope.schema.interfaces import IIterableSource
  >>> ztapi.provideAdapter(IIterableSource, ITerms, LoopsTerms,
  ...                      with=(IBrowserRequest,))
      
  >>> sorted((t.title, t.token) for t in view.conceptTypes())
  [(u'Topic', '.loops/concepts/topic'), (u'Type', '.loops/concepts/type'),
      (u'Unknown Type', '.loops/concepts/unknown')]
          
  >>> sorted((t.title, t.token) for t in view.predicates())
  [(u'has type', '.loops/concepts/hasType'),
      (u'subconcept', '.loops/concepts/standard')]

Searchable Text Adapter
-----------------------

  >>> from loops.concept import SearchableText
  >>> SearchableText(cc2).searchableText()
  u'cc2 Zope 3'

Resources and what they have to do with Concepts
================================================

  >>> from loops.interfaces import IDocument, IMediaAsset

We first need a resource manager:
    
  >>> from loops.resource import ResourceManager
  >>> loopsRoot['resources'] = ResourceManager()
  >>> resources = loopsRoot['resources']

A common type of resource is a document:
      
  >>> from loops.interfaces import IDocument
  >>> from loops.resource import Document
  >>> doc1 = Document(u'Zope Info')
  >>> resources['doc1'] = doc1
  >>> doc1.title
  u'Zope Info'
  >>> doc1.data
  u''
  >>> doc1.contentType
  ''

Another one is a media asset:

  >>> from loops.interfaces import IMediaAsset
  >>> from loops.resource import MediaAsset
  >>> img = MediaAsset(u'A png Image')

For testing we use some simple files from the tests directory:
      
  >>> from loops import tests
  >>> import os
  >>> path = os.path.join(*tests.__path__)
  >>> img.data = open(os.path.join(path, 'test_icon.png')).read()
  >>> img.getSize()
  381
  >>> img.getImageSize()
  (16, 16)
  >>> img.contentType
  'image/png'

  >>> pdf = MediaAsset(u'A pdf File')
  >>> pdf.data = open(os.path.join(path, 'test.pdf')).read()
  >>> pdf.getSize()
  25862
  >>> pdf.getImageSize()
  (-1, -1)
  >>> pdf.contentType
  'application/pdf'

We can associate a resource with a concept by assigning it to the concept:

  >>> cc1.assignResource(doc1)
  >>> res = cc1.getResources()
  >>> list(res)
  [<loops.resource.Document ...>]

The resource also provides access to the associated concepts (or views, see
below) via the getClients() method:

  >>> conc = doc1.getClients()
  >>> len(conc)
  1
  >>> conc[0] is cc1
  True


Views/Nodes: Menus, Menu Items, Listings, Pages, etc
====================================================

Note: the term "view" here is not directly related to the special
Zope 3 term "view" (a multiadapter for presentation purposes) but basically
bears the common sense meaning: an object (that may be persistent or
created on the fly) that provides a view to content of whatever kind.

Views (or nodes - that's the only type of views existing at the moment)
thus provide the presentation space for concepts and resources, i.e. visitors
of a site only see views or nodes but never concepts or resources directly;
the views or nodes, however, present informations coming from the concepts
or resources they are related to.

We first need a view manager:
    
  >>> from loops.view import ViewManager, Node
  >>> from zope.security.checker import NamesChecker, defineChecker
  >>> nodeChecker = NamesChecker(('body',))
  >>> defineChecker(Node, nodeChecker)

  >>> loopsRoot['views'] = ViewManager()
  >>> views = loopsRoot['views']

The view space is typically built up with nodes; a node may be a top-level
menu that may contain other nodes as menu or content items:
      
  >>> m1 = Node(u'Menu')
  >>> views['m1'] = m1
  >>> m11 = Node(u'Zope')
  >>> m1['m11'] = m11
  >>> m111 = Node(u'Zope in General')
  >>> m11['m111'] = m111
  >>> m112 = Node(u'Zope 3')
  >>> m11['m112'] = m112
  >>> m112.title
  u'Zope 3'
  >>> m112.description
  u''

There are a few convienence methods for accessing parent and child nodes:

  >>> m1.getParentNode() is None
  True
  >>> m11.getParentNode() is m1
  True
  >>> [zapi.getName(child) for child in m11.getChildNodes()]
  [u'm111', u'm112']

What is returned by these may be controlled by the nodeType attribute:

  >>> m1.nodeType = 'menu'
  >>> m11.nodeType = 'page'
  >>> m11.getParentNode('menu') is m1
  True
  >>> m11.getParentNode('page') is None
  True
  >>> m111.nodeType = 'info'
  >>> m112.nodeType = 'text'
  >>> len(list(m11.getChildNodes('text')))
  1

There are also shortcut methods to retrieve certain types of nodes
in a simple and logical way:

  >>> m1.getMenu() is m1
  True
  >>> m111.getMenu() is m1
  True
  >>> m1.getPage() is m1
  True
  >>> m111.getPage() is m111
  True
  >>> m112.getPage() is m11
  True
  >>> len(list(m1.getMenuItems()))
  1
  >>> len(list(m11.getMenuItems()))
  0
  >>> len(list(m111.getMenuItems()))
  0
  >>> len(list(m1.getTextItems()))
  0
  >>> len(list(m11.getTextItems()))
  1
  >>> len(list(m111.getTextItems()))
  0

Targets
-------

We can associate a node with a concept or directly with a resource via the
view class's target attribute. (We also have to supply a subscriber to
IRelationInvalidatedEvent to make sure associated actions will be carried
out - this is usually done through ZCML.)

  >>> from loops.util import removeTargetRelation
  >>> from loops.interfaces import ITargetRelation
  >>> from cybertools.relation.interfaces import IRelationInvalidatedEvent
  >>> ztapi.subscribe([ITargetRelation, IRelationInvalidatedEvent], None,
  ...                 removeTargetRelation)
  
  >>> m111.target = cc1
  >>> m111.target is cc1
  True
  >>> m111.target = cc1
  >>> m111.target is cc1
  True
  >>> m111.target = cc2
  >>> m111.target is cc2
  True

Node Views
----------

  >>> from loops.interfaces import INode
  >>> from loops.browser.node import NodeView
  >>> view = NodeView(m11, TestRequest())

  >>> page = view.page
  >>> items = page.textItems()
  >>> for item in items:
  ...     print item.url, item.editable
  http://127.0.0.1/loops/views/m1/m11/m112 False

  >>> menu = view.menu
  >>> items = menu.menuItems()
  >>> for item in items:
  ...     print item.url, view.selected(item)
  http://127.0.0.1/loops/views/m1/m11 True

Node Configuration
------------------

When configuring a node you may specify what you want to do with respect
to the node's target: associate an existing one or create a new one.
These options are provided via the INodeConfigSchema that is provided
by a NodeConfigAdapter; in addition the attributes of the node (like the
title) may be changed via the NodeConfigAdapter.
  
  >>> from loops.interfaces import INodeConfigSchema
  >>> from loops.view import NodeConfigAdapter
  >>> ztapi.provideAdapter(INode, INodeConfigSchema, NodeConfigAdapter)
  >>> nodeConfig = INodeConfigSchema(m111)

  >>> nodeConfig.title = u'New title for m111'
  >>> nodeConfig.title
  u'New title for m111'
  >>> m111.title
  u'New title for m111'
  >>> nodeConfig.target = doc1
  >>> m111.target is doc1
  True
  >>> m111 in doc1.getClients()
  True

The targetUri and targetType fields are only relevant when creating
a new target object:

  >>> nodeConfig.targetUri
  ''
  >>> nodeConfig.targetType
  'loops.resource.Document'

The node configuration form provides a target assignment field using
a vocabulary (source) for selecting the target. (In a future version this form
will be extended by a widget that lets you search for potential target
objects.) The source is basically a source list:

  >>> from loops.target import TargetSourceList
  >>> source = TargetSourceList(m111)
  >>> len(source)
  1
  >>> sorted([zapi.getName(s) for s in source])
  [u'doc1']

The form then uses a sort of browser view providing the ITerms interface
based on this source list:

  >>> terms = LoopsTerms(source, TestRequest())
  >>> term = terms.getTerm(doc1)
  >>> term.token, term.title, term.value
  ('.loops/resources/doc1', u'Zope Info', <loops.resource.Document...>)
      
  >>> term = terms.getTerm(cc1)
  >>> term.token, term.title, term.value
  ('.loops/concepts/cc1', u'cc1', <loops.concept.Concept...>)
      
  >>> terms.getValue('.loops/concepts/cc1') is cc1
  True

There is a special edit view class that can be used to configure a node
in a way that allows the creation of a target object on the fly.
(We here use the base class providing the method for this action; the real
application uses a subclass that does all the other stuff for form handling.)
When creating a new target object you may specify a uri that determines
the location of the new target object and its name.

  >>> from loops.browser.node import ConfigureBaseView
  >>> view = ConfigureBaseView(INodeConfigSchema(m111), TestRequest())
  >>> view.checkCreateTarget()
  >>> sorted(resources.keys())
  [u'doc1']
  >>> form = {'field.createTarget': True,
  ...         'field.targetUri': '.loops/resources/ma07',
  ...         'field.targetType': 'loops.resource.MediaAsset'}
  >>> view = ConfigureBaseView(m111, TestRequest(form=form))
  >>> m111.target = view.checkCreateTarget()
  >>> sorted(resources.keys())
  [u'doc1', u'ma07']
  >>> isinstance(resources['ma07'], MediaAsset)
  True
  
  >>> form = {'field.createTarget': True,
  ...         'field.targetType': 'loops.resource.Document'}
  >>> view = ConfigureBaseView(m111, TestRequest(form=form))
  >>> m111.target = view.checkCreateTarget()
  >>> sorted(resources.keys())
  [u'doc1', u'm1.m11.m111', u'ma07']
  >>> isinstance(resources['m1.m11.m111'], Document)
  True
        
A node object provides the targetSchema of its target:

  >>> from loops.interfaces import IDocumentView
  >>> from loops.interfaces import IMediaAssetView
  >>> IDocumentView.providedBy(m111)
  True
  >>> IMediaAssetView.providedBy(m111)
  False
  >>> m111.target = None
  >>> IDocumentView.providedBy(m111)
  False
  >>> m111.target = resources['ma07']
  >>> IDocumentView.providedBy(m111)
  False
  >>> IMediaAssetView.providedBy(m111)
  True

A node's target is rendered using the NodeView's renderTargetBody()
method. This makes use of a browser view registered for the target interface,
and of a lot of other stuff needed for the rendering machine.

  >>> from zope.app.publisher.interfaces.browser import IBrowserView
  >>> from loops.browser.resource import DocumentView
  >>> ztapi.provideAdapter(IDocument, Interface, DocumentView,
  ...                      with=(IBrowserRequest,))

  >>> from zope.component.interfaces import IFactory
  >>> from zope.app.renderer import rest
  >>> ztapi.provideUtility(IFactory, rest.ReStructuredTextSourceFactory,
  ...                      'zope.source.rest')
  >>> ztapi.provideAdapter(rest.IReStructuredTextSource, Interface,
  ...                      rest.ReStructuredTextToHTMLRenderer,
  ...                      with=(IBrowserRequest,))

  >>> m112.target = doc1
  >>> view = NodeView(m112, TestRequest())
  >>> view.renderTargetBody()
  u''
  >>> doc1.data = u'Test data\n\nAnother paragraph'
  >>> view.renderTargetBody()
  u'Test data\n\nAnother paragraph'
  >>> doc1.contentType = 'text/restructured'
  >>> view.renderTargetBody()
  u'<p>Test data</p>\n<p>Another paragraph</p>\n'

It is possible to edit a target's attributes directly in an
edit form provided by the node:

  >>> from loops.target import DocumentProxy, MediaAssetProxy
  >>> ztapi.provideAdapter(INode, IDocumentView, DocumentProxy)
  >>> ztapi.provideAdapter(INode, IMediaAssetView, MediaAssetProxy)

  >>> proxy = zapi.getAdapter(m111, IDocumentView)
  >>> proxy.title = u'Set via proxy'
  >>> resources['ma07'].title
  u'Set via proxy'

If the target object is removed from its container all references
to it are removed as well. (To make this work we have to handle
the IObjectRemovedEvent; this is usually done via ZCML in the
cybertools.relation package.)

  >>> from zope.app.container.interfaces import IObjectRemovedEvent
  >>> from zope.interface import Interface
  >>> from cybertools.relation.registry import invalidateRelations
  >>> ztapi.subscribe([Interface, IObjectRemovedEvent], None,
  ...                 invalidateRelations)

  >>> del resources['ma07']
  >>> m111.target
  >>> IMediaAssetView.providedBy(m111)
  False

Ordering Nodes
--------------

Note: this functionality has been moved to cybertools.container; we
include some testing here to make sure it still works and give a short
demonstration.

Let's add some more nodes and reorder them:

  >>> m113 = Node()
  >>> m11['m113'] = m113
  >>> m114 = Node()
  >>> m11['m114'] = m114
  >>> m11.keys()
  ['m111', 'm112', 'm113', 'm114']
      
A special management view provides methods for moving objects down, up,
to the bottom, and to the top.
      
  >>> from cybertools.container.ordered import OrderedContainerView
  >>> view = OrderedContainerView(m11, TestRequest())
  >>> view.move_bottom(('m113',))
  >>> m11.keys()
  ['m111', 'm112', 'm114', 'm113']
  >>> view.move_up(('m114',), 1)
  >>> m11.keys()
  ['m111', 'm114', 'm112', 'm113']

Import/Export
-------------

Nodes may be exported to and loaded from external sources, typically
file representations that allow the transfer of nodes from one Zope
instance to another.

  >>> from loops.external import NodesLoader
  >>> loader = NodesLoader(views)
  >>> data = [{'name': 'm2', 'path': '', 'description': u'desc 1',
  ...          'title': u'M 2', 'body': u'test m2', 'nodeType': 'menu' },
  ...         {'name': 'm21', 'path': 'm2', 'description': u'',
  ...          'title': u'M 21', 'body': u'test m21', 'nodeType': 'page' },
  ...         {'name': 'm114', 'path': 'm1/m11', 'description': u'',
  ...          'title': u'M 114', 'body': u'test m114', 'nodeType': 'page' },]
  >>> loader.load(data)
  >>> views['m2']['m21'].title
  u'M 21'
  >>> views['m1']['m11']['m114'].title
  u'M 114'

  >>> from loops.external import NodesExporter, NodesImporter
  >>> exporter = NodesExporter(views)
  >>> data = exporter.extractData()
  >>> len(data)
  8
  >>> data[3]['path']
  u'm1/m11'
  >>> data[3]['name']
  u'm112'

  >>> dumpname = os.path.dirname(__file__) + '/test.tmp'
  >>> exporter.filename = dumpname
  >>> exporter.dumpData()

Load them again from the exported file:
  
  >>> importer = NodesImporter(views)
  >>> importer.filename = dumpname
  >>> imported = importer.getData()
  >>> imported == data
  True

  >>> loader.load(imported)


Fin de partie
=============

  >>> os.unlink(dumpname)
  >>> placefulTearDown()

