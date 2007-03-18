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
  >>> from loops.resource import Resource

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> component.provideUtility(DummyRelationRegistry())
  >>> from cybertools.relation.tests import IntIdsStub
  >>> intIds = IntIdsStub()
  >>> component.provideUtility(intIds)

  >>> from loops.type import LoopsType, ConceptType, TypeConcept
  >>> component.provideAdapter(LoopsType)
  >>> component.provideAdapter(ConceptType)
  >>> component.provideAdapter(TypeConcept)

  >>> from loops import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.setup import SetupManager
  >>> from loops.organize.setup import SetupManager as OrganizeSetupManager
  >>> component.provideAdapter(OrganizeSetupManager, name='organize')
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()

Let's look what setup has provided us with:

  >>> sorted(concepts)
  [u'domain', u'file', u'hasType', u'note', u'person', u'predicate', u'query',
   u'standard', u'textdocument', u'type']

Now let's add a few more concepts:

  >>> topic = concepts[u'topic'] = Concept(u'Topic')
  >>> intIds.register(topic)
  9
  >>> zope = concepts[u'zope'] = Concept(u'Zope')
  >>> zope.conceptType = topic
  >>> intIds.register(zope)
  10
  >>> zope3 = concepts[u'zope3'] = Concept(u'Zope 3')
  >>> zope3.conceptType = topic
  >>> intIds.register(zope3)
  11

Navigation typically starts at a start object, which by default ist the
domain concept (if present, otherwise the top-level type concept):

  >>> from loops.xmlrpc.common import LoopsMethods
  >>> xrf = LoopsMethods(loopsRoot, TestRequest())
  >>> startObj = xrf.getStartObject()
  >>> sorted(startObj.keys())
  ['children', 'description', 'id', 'name', 'parents', 'resources',
   'title', 'type', 'viewName']
  >>> startObj['id'], startObj['name'], startObj['title'], startObj['type']
  ('1', u'domain', u'Domain', '0')

There are a few standard objects we can retrieve directly:

  >>> defaultPred = xrf.getDefaultPredicate()
  >>> defaultPred['id'], defaultPred['name']
  ('7', u'standard')
  >>> typePred = xrf.getTypePredicate()
  >>> typePred['id'], typePred['name']
  ('6', u'hasType')
  >>> typeConcept = xrf.getTypeConcept()
  >>> typeConcept['id'], typeConcept['name']
  ('0', u'type')

In addition we can get a list of all types and all predicates available:

  >>> sorted(t['name'] for t in xrf.getConceptTypes())
  [u'domain', u'file', u'person', u'predicate', u'query', u'textdocument', u'type']
  >>> sorted(t['name'] for t in xrf.getPredicates())
  [u'hasType', u'standard']

We can also retrieve a certain object by its id or its name:

  >>> obj2 = xrf.getObjectById('2')
  >>> obj2['id'], obj2['name']
  ('2', u'query')
  >>> textdoc = xrf.getObjectByName(u'textdocument')
  >>> textdoc['id'], textdoc['name']
  ('4', u'textdocument')

All methods that retrieve one object also returns its children and parents:

  >>> ch = typeConcept['children']
  >>> len(ch)
  1
  >>> ch[0]['name']
  u'hasType'
  >>> sorted(c['name'] for c in ch[0]['objects'])
  [u'domain', u'file', u'person', u'predicate', u'query', u'textdocument', u'type']

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
  [u'domain', u'file', u'person', u'predicate', u'query', u'textdocument', u'type']

  >>> pa = xrf.getParents('6')
  >>> len(pa)
  1
  >>> pa[0]['name']
  u'hasType'
  >>> sorted(p['name'] for p in pa[0]['objects'])
  [u'predicate']

Resources
---------

  >>> from loops.resource import TextDocumentAdapter
  >>> from loops.interfaces import IResource, ITextDocument
  >>> component.provideAdapter(TextDocumentAdapter, (IResource,), ITextDocument)

  >>> zope3Id = xrf.getObjectByName('zope3')['id']
  >>> td01 = resources['td01'] = Resource(u'Doc1')
  >>> td01.resourceType = concepts['textdocument']
  >>> zope3.assignResource(td01)

  >>> obj = xrf.getObjectById(zope3Id)
  >>> obj['resources'][0]['objects'][0]['title']
  u'Doc1'

Attributes
----------

  >>> from loops.organize.party import Person
  >>> from loops.organize.interfaces import IPerson
  >>> component.provideAdapter(Person, provides=IPerson)
  >>> p01 = concepts['p01'] = Concept(u'John Smith')
  >>> p01.conceptType = concepts['person']

  >>> john = xrf.getObjectByName('p01')
  >>> #john

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
  {'description': u'', 'title': u'Zope 2', 'type': '9', 'id': '15',
   'name': u'zope2'}

Changing the attributes of a concept
------------------------------------

  >>> xrf.editConcept(john['id'], 'firstName', u'John')
  'OK'
  >>> john = xrf.getObjectById(john['id'])
  >>> john['firstName']
  u'John'
  >>> john['lastName']
  u''


Fin de partie
=============

  >>> placefulTearDown()

