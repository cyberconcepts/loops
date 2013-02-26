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
  >>>

and set up a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.setup import addObject
  >>> from loops.organize.setup import SetupManager as OrganizeSetupManager
  >>> component.provideAdapter(OrganizeSetupManager, name='organize')
  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> from loops import util
  >>> loopsRoot = site['loops']
  >>> loopsId = util.getUidForObject(loopsRoot)

  >>> from loops.knowledge.tests import importData
  >>> importData(loopsRoot)

Let's look what setup has provided us with:

  >>> len(concepts)
  22

Now let's add a few more concepts:

  >>> topic = concepts[u'topic']
  >>> zope = addObject(concepts, Concept, 'zope', title=u'Zope', conceptType=topic)
  >>> zope3 = addObject(concepts, Concept, 'zope3', title=u'Zope 3', conceptType=topic)

Navigation typically starts at a start object, which by default ist the
domain concept (if present, otherwise the top-level type concept):

  >>> from loops.xmlrpc.common import LoopsMethods
  >>> xrf = LoopsMethods(loopsRoot, TestRequest())
  >>> startObj = xrf.getStartObject()
  >>> sorted(startObj.keys())
  ['children', 'description', 'id', 'name', 'parents', 'resources',
   'title', 'type', 'viewName']
  >>> startObj['id'], startObj['name'], startObj['title'], startObj['type']
  ('3', u'domain', u'Domain', '0')

There are a few standard objects we can retrieve directly:

  >>> defaultPred = xrf.getDefaultPredicate()
  >>> defaultPred['id'], defaultPred['name']
  ('14', u'standard')
  >>> typePred = xrf.getTypePredicate()
  >>> typePred['id'], typePred['name']
  ('2', u'hasType')
  >>> typeConcept = xrf.getTypeConcept()
  >>> typeConcept['id'], typeConcept['name']
  ('0', u'type')

In addition we can get a list of all types and all predicates available;
note that the 'hasType' predicate is not shown as it should not be
applied in an explicit assignment.

  >>> sorted(t['name'] for t in xrf.getConceptTypes())
  [u'competence', u'customer', u'domain', u'file', u'note', u'person', 
   u'predicate', u'task', u'textdocument', u'topic', u'type']
  >>> sorted(t['name'] for t in xrf.getPredicates())
  [u'depends', u'issubtype', u'knows', u'ownedby', u'provides', u'requires', 
   u'standard']

We can also retrieve a certain object by its id or its name:

  >>> obj2 = xrf.getObjectById('3')
  >>> obj2['id'], obj2['name']
  ('3', u'domain')
  >>> textdoc = xrf.getObjectByName(u'textdocument')
  >>> textdoc['id'], textdoc['name']
  ('9', u'textdocument')

All methods that retrieve one object also returns its children and parents:

  >>> ch = typeConcept['children']
  >>> len(ch)
  1
  >>> ch[0]['name']
  u'hasType'
  >>> sorted(c['name'] for c in ch[0]['objects'])
  [u'competence', u'customer', u'domain', u'file', u'note', u'person', 
   u'predicate', u'task', u'textdocument', u'topic', u'type']

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
  [u'competence', u'customer', u'domain', u'file', u'note', u'person', 
   u'predicate', u'task', u'textdocument', u'topic', u'type']

  >>> pa = xrf.getParents('5')
  >>> len(pa)
  1
  >>> pa[0]['name']
  u'hasType'
  >>> sorted(p['name'] for p in pa[0]['objects'])
  [u'type']

Resources
---------

  >>> from loops.resource import TextDocumentAdapter
  >>> from loops.interfaces import IResource, ITextDocument, IFile
  >>> component.provideAdapter(TextDocumentAdapter, (IResource,), ITextDocument)
  >>> from loops.resource import FileAdapter
  >>> component.provideAdapter(FileAdapter, provides=IFile)

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
  >>> xrf.assignChild(zopeId, defaultPred['id'], zope3Id)
  'OK'
  >>> pa = xrf.getParents(zope3Id)
  >>> len(pa)
  2

  >>> xrf.deassignChild(zopeId, defaultPred['id'], zope3Id)
  'OK'
  >>> pa = xrf.getParents(zope3Id)
  >>> len(pa)
  1

  >>> topicId = xrf.getObjectByName('topic')['id']
  >>> xrf.createConcept(topicId, u'zope2', u'Zope 2')
  {'description': u'', 'title': u'Zope 2', 'type': '36', 'id': '72',
   'name': u'zope2'}

The name of the concept is checked by a name chooser; if the corresponding
parameter is empty, the name will be generated from the title.

  >>> xrf.createConcept(topicId, u'', u'Python')
  {'description': u'', 'title': u'Python', 'type': '36', 'id': '74',
   'name': u'python'}

If we try to deassign a ``hasType`` relation nothing will happen; a
corresponding error value will be returned.

  >>> xrf.deassignChild(topicId, typePred['id'], zope3Id)
  'Not allowed'

Changing the attributes of a concept
------------------------------------

  >>> from loops.knowledge.knowledge import Person
  >>> from loops.knowledge.interfaces import IPerson
  >>> component.provideAdapter(Person, provides=IPerson)

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

