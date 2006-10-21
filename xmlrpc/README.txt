===============================================================
loops.xmlrpc
===============================================================

  ($Id$)

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

  >>> from loops import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.setup import SetupManager
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()

Let's look what setup has provided us with:

  >>> list(concepts)
  [u'file', u'hasType', u'image', u'predicate', u'standard', u'textdocument', u'type']

Navigation typically starts at a start object, which by default ist the
top-level type concept:

  >>> from loops.xmlrpc.common import LoopsMethods
  >>> xrf = LoopsMethods(loopsRoot, TestRequest())
  >>> xrf.getStartObject()
  {'title': u'Type', 'type': '0', 'id': '0', 'name': u'type'}

If we provide a concept named "domain" this will be used as starting point:

  >>> from loops.concept import Concept
  >>> domain = concepts[u'domain'] = Concept(u'Domain')
  >>> domain.conceptType = concepts.getTypeConcept()
  >>> xrf.getStartObject()
  {'title': u'Domain', 'type': '0', 'id': '7', 'name': u'domain'}

There are a few standard objects we can retrieve directly:

  >>> xrf.getDefaultPredicate()
  {'title': u'subobject', 'type': '4', 'id': '6', 'name': u'standard'}
  >>> xrf.getTypePredicate()
  {'title': u'has Type', 'type': '4', 'id': '5', 'name': u'hasType'}
  >>> xrf.getTypeConcept()
  {'title': u'Type', 'type': '0', 'id': '0', 'name': u'type'}

In addition we can get a list of all types and all predicates available:

  >>> sorted(t['name'] for t in xrf.getConceptTypes())
  [u'domain', u'file', u'image', u'predicate', u'textdocument', u'type']
  >>> sorted(t['name'] for t in xrf.getPredicates())
  [u'hasType', u'standard']

We can also retrieve a certain object by its id or its name:

  >>> xrf.getObjectById('2')
  {'title': u'Image', 'type': '0', 'id': '2', 'name': u'image'}
  >>> xrf.getObjectByName(u'textdocument')
  {'title': u'Text Document', 'type': '0', 'id': '3', 'name': u'textdocument'}

Now we are ready to deal with children and parents...

  >>> ch = xrf.getChildren('0')
  >>> len(ch)
  1
  >>> ch[0]['name']
  u'hasType'
  >>> sorted(c['name'] for c in ch[0]['objects'])
  [u'domain', u'file', u'image', u'predicate', u'textdocument', u'type']

  >>> pa = xrf.getParents('6')
  >>> len(pa)
  1
  >>> pa[0]['name']
  u'hasType'
  >>> sorted(p['name'] for p in pa[0]['objects'])
  [u'predicate']


Fin de partie
=============

  >>> placefulTearDown()

