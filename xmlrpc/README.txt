===============================================================
loops.xmlrpc
===============================================================

  ($Id$)

Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface
  >>> from zope.publisher.browser import TestRequest
  >>> from loops.concept import Concept

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> component.provideUtility(DummyRelationRegistry())
  >>> from cybertools.relation.tests import IntIdsStub
  >>> intIds = IntIdsStub()
  >>> component.provideUtility(intIds)

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

Now let's add a few more concepts:

  >>> topic = concepts[u'topic'] = Concept(u'Topic')
  >>> intIds.register(topic)
  7
  >>> zope = concepts[u'zope'] = Concept(u'Zope')
  >>> zope.conceptType = topic
  >>> intIds.register(zope)
  8
  >>> zope3 = concepts[u'zope3'] = Concept(u'Zope 3')
  >>> zope3.conceptType = topic
  >>> intIds.register(zope3)
  9

Navigation typically starts at a start object, which by default ist the
top-level type concept:

  >>> from loops.xmlrpc.common import LoopsMethods
  >>> xrf = LoopsMethods(loopsRoot, TestRequest())
  >>> startObj = xrf.getStartObject()
  >>> sorted(startObj.keys())
  ['children', 'id', 'name', 'parents', 'title', 'type']
  >>> startObj['id'], startObj['name'], startObj['title'], startObj['type']
  ('0', u'type', u'Type', '0')

If we provide a concept named "domain" this will be used as starting point:

  >>> from loops.concept import Concept
  >>> domain = concepts[u'domain'] = Concept(u'Domain')
  >>> domain.conceptType = concepts.getTypeConcept()
  >>> startObj = xrf.getStartObject()
  >>> sorted(startObj.keys())
  ['children', 'id', 'name', 'parents', 'title', 'type']
  >>> startObj['id'], startObj['name'], startObj['title'], startObj['type']
  ('10', u'domain', u'Domain', '0')

There are a few standard objects we can retrieve directly:

  >>> defaultPred = xrf.getDefaultPredicate()
  >>> defaultPred['id'], defaultPred['name']
  ('6', u'standard')
  >>> typePred = xrf.getTypePredicate()
  >>> typePred['id'], typePred['name']
  ('5', u'hasType')
  >>> typeConcept = xrf.getTypeConcept()
  >>> typeConcept['id'], typeConcept['name']
  ('0', u'type')

In addition we can get a list of all types and all predicates available:

  >>> sorted(t['name'] for t in xrf.getConceptTypes())
  [u'domain', u'file', u'image', u'predicate', u'textdocument', u'type']
  >>> sorted(t['name'] for t in xrf.getPredicates())
  [u'hasType', u'standard']

We can also retrieve a certain object by its id or its name:

  >>> obj2 = xrf.getObjectById('2')
  >>> obj2['id'], obj2['name']
  ('2', u'image')
  >>> textdoc = xrf.getObjectByName(u'textdocument')
  >>> textdoc['id'], textdoc['name']
  ('3', u'textdocument')

All methods that retrieve one object also returns its children and parents:

  >>> ch = typeConcept['children']
  >>> len(ch)
  1
  >>> ch[0]['name']
  u'hasType'
  >>> sorted(c['name'] for c in ch[0]['objects'])
  [u'domain', u'file', u'image', u'predicate', u'textdocument', u'type']

  >>> pa = defaultPred['parents']
  >>> len(pa)
  1
  >>> pa[0]['name']
  u'hasType'
  >>> sorted(p['name'] for p in pa[0]['objects'])
  [u'predicate']

We can also retrieve children and parents explicitely:

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

Updating the concept map
------------------------

  >>> zopeId = xrf.getObjectByName('zope')['id']
  >>> zope3Id = xrf.getObjectByName('zope3')['id']
  >>> xrf.assignChild(zopeId, zope3Id, defaultPred['id'])
  'OK'

  >>> xrf.deassignChild(zopeId, zope3Id, defaultPred['id'])
  'OK'

  >>> topicId = xrf.getObjectByName('topic')['id']
  >>> xrf.createConcept(topicId, u'zope2', u'Zope 2')
  '12'


Fin de partie
=============

  >>> placefulTearDown()

