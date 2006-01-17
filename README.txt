===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  
  >>> from zope.app import zapi
  >>> from zope.app.tests import ztapi
  >>> from zope.publisher.browser import TestRequest
  

Concepts and Relations
======================

Let's start with creating a few example concepts, putting them in a
top-level loops container and a concept manager:

  >>> from loops import Loops
  >>> loops = Loops()
  >>> site['loops'] = Loops()
  >>> loops = site['loops']

  >>> from loops.concept import ConceptManager, Concept
  >>> loops['concepts'] = ConceptManager()
  >>> concepts = loops['concepts']
  >>> zope = Concept()
  >>> concepts['zope'] = zope
  >>> zope.title
  u''

  >>> zope3 = Concept(u'Zope 3')
  >>> concepts['zope3'] = zope3
  >>> zope3.title
  u'Zope 3'

Now we want to relate the second concept to the first one.

In order to do this we first have to provide a relations registry. For
testing we use a simple dummy implementation.

  >>> from cybertools.relation.interfaces import IRelationsRegistry
  >>> from cybertools.relation.registry import DummyRelationsRegistry
  >>> from zope.app.testing import ztapi
  >>> ztapi.provideUtility(IRelationsRegistry, DummyRelationsRegistry())

Now we can assign the concept c2 to c1 (using the standard ConceptRelation):
        
  >>> zope.assignConcept(zope3)

We can now ask our concepts for their related concepts:

  >>> sc1 = zope.getSubConcepts()
  >>> len(sc1)
  1
  >>> zope3 in sc1
  True
  >>> len(zope.getParentConcepts())
  0

  >>> pc2 = zope3.getParentConcepts()
  >>> len(pc2)
  1

  >>> zope in pc2
  True
  >>> len(zope3.getSubConcepts())
  0

TODO: Work with views...
        

Resources and what they have to do with Concepts
================================================

We first need a resource manager:
    
  >>> from loops.resource import ResourceManager, Document
  >>> loops['resources'] = ResourceManager()
  >>> resources = loops['resources']

A common type of resource is a Document:
      
  >>> zope_info = Document(u'Zope Info')
  >>> resources['zope_info'] = zope_info
  >>> zope_info.title
  u'Zope Info'
  >>> zope_info.body
  u''
  >>> zope_info.format
  u'text/xml'

We can associate a resource with a concept by assigning it to the concept:

  >>> zope.assignResource(zope_info)
  >>> res = zope.getResources()
  >>> list(res)
  [<loops.resource.Document ...>]

The resource also provides access to the associated concepts (or views, see
below) via the getClients() method:

  >>> conc = zope_info.getClients()
  >>> len(conc)
  1
  >>> conc[0] is zope
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

  >>> loops['views'] = ViewManager()
  >>> views = loops['views']

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
  >>> len(m11.getChildNodes('text'))
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
  >>> len(m1.getMenuItems())
  1
  >>> len(m11.getMenuItems())
  0
  >>> len(m111.getMenuItems())
  0
  >>> len(m1.getTextItems())
  0
  >>> len(m11.getTextItems())
  1
  >>> len(m111.getTextItems())
  0

Targets
-------

We can associate a node with a concept or directly with a resource via the
view class's target attribute:

  >>> m111.target = zope_info
  >>> m111.target is zope_info
  True
  >>> m111.target = zope_info
  >>> m111.target is zope_info
  True
  >>> m111.target = zope3
  >>> m111.target is zope3
  True

Node views
----------

  >>> from loops.browser.node import NodeView
  >>> view = NodeView(m11, TestRequest())

  >>> page = view.page()
  >>> items = page.textItems()
  >>> for item in items:
  ...     print item.url, item.editable
  http://127.0.0.1/loops/views/m1/m11/m112 False

  >>> menu = view.menu()
  >>> items = menu.menuItems()
  >>> for item in items:
  ...     print item.url, view.selected(item)
  http://127.0.0.1/loops/views/m1/m11 True

    
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

  >>> import os
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

