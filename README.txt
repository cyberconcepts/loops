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

Views: Menus, Menu Items, Listings, Simple Content, etc
=======================================================

We first need a view manager:
    
  >>> from loops.view import ViewManager, Node
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


Fin de partie
=============

  >>> placefulTearDown()

