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

  >>> cc2 = Concept(u'Zope 3')
  >>> concepts['cc2'] = cc2
  >>> cc2.title
  u'Zope 3'

Now we want to relate the second concept to the first one.

In order to do this we first have to provide a relations registry. For
testing we use a simple dummy implementation.

  >>> from cybertools.relation.interfaces import IRelationsRegistry
  >>> from cybertools.relation.registry import DummyRelationsRegistry
  >>> from zope.app.testing import ztapi
  >>> ztapi.provideUtility(IRelationsRegistry, DummyRelationsRegistry())

Now we can assign the concept c2 to c1 (using the standard ConceptRelation):
        
  >>> cc1.assignConcept(cc2)

We can now ask our concepts for their related concepts:

  >>> sc1 = cc1.getSubConcepts()
  >>> len(sc1)
  1
  >>> cc2 in sc1
  True
  >>> len(cc1.getParentConcepts())
  0

  >>> pc2 = cc2.getParentConcepts()
  >>> len(pc2)
  1

  >>> cc1 in pc2
  True
  >>> len(cc2.getSubConcepts())
  0

TODO: Work with views...
        

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
Zop 3 term "view" (a multiadapter for presentation purposes) but basically
bears the common sense meaning: an object (that may be persistent or
created on the fly) that provides a view to content of whatever kind.

Views (or nodes - that's the only type of views existing at the moment)
thus provide the presentation space to concepts and resources.

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
view class's target attribute:

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

Node Schema Adapters
--------------------

When creating or editing (more precisely: configuring) a node you may
specify what you want to do with respect to the node's target: associate
an existing one or create a new one (with specifying the target's type),
and give an URI that will be used to identify the target. (Internally
the reference to the target will be stored as a relation so that the
target may be moved or renamed without any problems.)

  >>> from loops.interfaces import INodeConfigSchema
  >>> from loops.view import NodeConfigAdapter
  >>> ztapi.provideAdapter(INode, INodeConfigSchema, NodeConfigAdapter)
  >>> nodeConfig = INodeConfigSchema(m111)

  >>> nodeConfig.targetUri
  u'.loops/concepts/cc2'
  >>> nodeConfig.title = u'New title for m111'
  >>> nodeConfig.title
  u'New title for m111'
  >>> m111.title
  u'New title for m111'
  >>> nodeConfig.targetUri = '.loops/resources/doc1'
  >>> nodeConfig.title = 'New title for m111'
  >>> m111.target is doc1
  True
  >>> nodeConfig.targetType
  'loops.resource.Document'
  >>> m111 in doc1.getClients()
  True

There is a special edit view class that can be used to configure a node
in a way, that allows the creation of a target object on the fly.
(We here use the base class providing the method for this action; the real
application uses a subclass that does all the other stuff for form handling.)

  >>> from loops.browser.node import ConfigureBaseView
  >>> view = ConfigureBaseView(INodeConfigSchema(m111), TestRequest())
  >>> view.checkCreateTarget()
  >>> sorted(resources.keys())
  [u'doc1']
  >>> form = {'field.createTarget': True,
  ...         'field.targetUri': '.loops/resources/ma07',
  ...         'field.targetType': 'loops.resource.MediaAsset'}
  >>> view = ConfigureBaseView(INodeConfigSchema(m111), TestRequest(form=form))
  >>> view = ConfigureBaseView(m111, TestRequest(form=form))
  >>> view.checkCreateTarget()
  >>> sorted(resources.keys())
  [u'doc1', u'ma07']

It is also possible to edit a target's attributes directly in an
edit form provided by the node:

  >>> from loops.target import DocumentProxy, MediaAssetProxy
  >>> ztapi.provideAdapter(INode, IDocument, DocumentProxy)
  >>> ztapi.provideAdapter(INode, IMediaAsset, MediaAssetProxy)

Ordering Nodes
--------------

Let's add some more nodes and reorder them:

  >>> m113 = Node()
  >>> m11['m113'] = m113
  >>> m114 = Node()
  >>> m11['m114'] = m114
  >>> m11.keys()
  ['m111', 'm112', 'm113', 'm114']
      
  >>> m11.moveSubNodesByDelta(['m113'], -1)
  >>> m11.keys()
  ['m111', 'm113', 'm112', 'm114']

A special management view provides methods for moving objects down, up,
to the bottom, and to the top
      
  >>> from loops.browser.node import OrderedContainerView
  >>> view = OrderedContainerView(m11, TestRequest())
  >>> view.moveToBottom(('m113',))
  >>> m11.keys()
  ['m111', 'm112', 'm114', 'm113']
  >>> view.moveUp(('m114',), 1)
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

