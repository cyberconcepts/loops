===============================================================
loops.xmlrpc
===============================================================

Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface
  >>> from zope.publisher.browser import TestRequest

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> component.provideUtility(DummyRelationRegistry())
  >>> from cybertools.relation.tests import IntIdsStub
  >>> component.provideUtility(IntIdsStub())

  >>> from loops.type import ConceptType, TypeConcept
  >>> component.provideAdapter(ConceptType)
  >>> component.provideAdapter(TypeConcept)

  >>> from loops.base import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.setup import SetupManager
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()

Let's look what setup has provided us with:

  >>> sorted(concepts)
  ['domain', 'file', 'hasType', 'note', 'predicate',
   'standard', 'textdocument', 'type']


loops Traversal
===============

The loops root object provides a traversal mechanism that goes beyond the
standard container traversal. One can directly access objects by their
unique id or via a symbolic name (like `startObject`); usually the traverser
returns a REST view of the object.

  >>> from loops.rest.traversal import LoopsTraverser
  >>> from zope.publisher.interfaces.browser import IBrowserPublisher
  >>> component.provideAdapter(LoopsTraverser, provides=IBrowserPublisher)

  >>> from loops.rest.common import ConceptView
  >>> component.provideAdapter(ConceptView)

Navigation typically starts at a start object, which by default ist the
domain type concept (or the top-level type concept, if there is no domain type):

  >>> request = TestRequest()
  >>> obj = LoopsTraverser(loopsRoot, request).publishTraverse(request, 'startObject')
  >>> obj
  <loops.rest.common.ConceptView object at ...>
  >>> obj.context.title
  'Domain'

The traversal adapter returns a view that when called renders the
representation of its context object:

  >>> obj()
  'Hello REST'


Fin de partie
=============

  >>> placefulTearDown()

