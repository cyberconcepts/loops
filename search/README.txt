===================================================================
loops.search - Provide search functionality for the loops framework
===================================================================

  ($Id$)


Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface
  >>> from zope.interface import implements

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> from cybertools.relation.tests import IntIdsStub
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations)
  >>> component.provideUtility(IntIdsStub())

  >>> from loops.type import ConceptType, TypeConcept
  >>> from loops.interfaces import ITypeConcept
  >>> component.provideAdapter(ConceptType)
  >>> component.provideAdapter(TypeConcept)

  >>> from loops import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.setup import SetupManager
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()
  >>> typeConcept = concepts['type']

  >>> from loops.concept import Concept
  >>> topic = concepts['topic'] = Concept(u'Topic')
  >>> for c in (topic,): c.conceptType = typeConcept
  >>> query = concepts['query']

In addition we create a concept that holds the search page and a node
(page) that links to this concept:

  >>> search = concepts['search'] = Concept(u'Search')
  >>> search.conceptType = query

  >>> from loops.view import Node
  >>> page = views['page'] = Node('Search Page')
  >>> page.target = search

Search views
------------

Now we are ready to create a search view object:

  >>> from zope.publisher.browser import TestRequest
  >>> from loops.search.browser import Search
  >>> searchView = Search(search, TestRequest())

The search view provides values for identifying the search form itself
and the parameter rows; the rowNum is auto-incremented, so it should be
accessed exactly once per row:

  >>> searchView.rowNum
  1
  >>> searchView.rowNum
  2

The search view provides vocabularies for types that allow the selection
of types to search for; this needs an ITypeManager adapter registered via
zcml in real life:

  >>> from loops.type import LoopsTypeManager
  >>> component.provideAdapter(LoopsTypeManager)

  >>> t = searchView.typesForSearch()
  >>> len(t)
  9
  >>> t.getTermByToken('loops:resource:*').title
  'Any Resource'

  >>> t = searchView.conceptTypesForSearch()
  >>> len(t)
  4
  >>> t.getTermByToken('loops:concept:*').title
  'Any Concept'

To execute the search in the context of a node we have to set up a node
view for our page. The submitReplacing method returns a JavaScript call
that will replace the results part on the search page; as this registers
the dojo library with the view's controller we also have to supply
a controller attribute for the search view.

  >>> from loops.browser.node import NodeView
  >>> request = TestRequest()
  >>> pageView = NodeView(page, request)

  >>> from cybertools.browser.liquid.controller import Controller
  >>> searchView.controller = Controller(searchView, request)

  >>> searchView.submitReplacing('1.results', '1.search.form', pageView)
  'return submitReplacing("1.results", "1.search.form",
       "http://127.0.0.1/loops/views/page/.target10/@@searchresults.html")'

Basic (text/title) search
-------------------------

The searchresults.html view, i.e. the SearchResults view class provides the
result set of the search via its `results` property.

Before accessing the `results` property we have to prepare a (for testing
purposes fairly primitive) catalog and a resource we can search for:

  >>> from zope.app.catalog.interfaces import ICatalog
  >>> class DummyCat(object):
  ...     implements(ICatalog)
  ...     def searchResults(self, **criteria):
  ...         result = []
  ...         name = criteria.get('loops_title')
  ...         if name and name.endswith('*'): name = name[:-1]
  ...         typeToken = criteria.get('loops_type', ('resource',))
  ...         if name or typeToken:
  ...             if 'concept' in typeToken[0]:
  ...                  if name:
  ...                      result = concepts.get(name)
  ...                  else:
  ...                      tp = concepts[typeToken[0].split(':')[-1]]
  ...                      result = list(tp.getChildren())
  ...             else:
  ...                 result = resources.get(name)
  ...         if not result: return []
  ...         return type(result) is list and result or [result]
  >>> component.provideUtility(DummyCat())

  >>> from loops.resource import Resource
  >>> rplone = resources['plone'] = Resource()

  >>> from loops.search.browser import SearchResults
  >>> form = {'search.2.title': True, 'search.2.text': u'plone'}
  >>> request = TestRequest(form=form)
  >>> resultsView = SearchResults(page, request)

  >>> results = list(resultsView.results)
  >>> len(results)
  1
  >>> results[0].context == rplone
  True

  >>> form = {'search.2.title': True, 'search.2.text': u'foo'}
  >>> request = TestRequest(form=form)
  >>> resultsView = SearchResults(page, request)
  >>> len(list(resultsView.results))
  0

Search via related concepts
---------------------------

We first have to prepare some test concepts (topics); we also assign our test
resource (rplone) from above to one of the topics:

  >>> czope = concepts['zope'] = Concept(u'Zope')
  >>> czope2 = concepts['zope2'] = Concept(u'Zope 2')
  >>> czope3 = concepts['zope3'] = Concept(u'Zope 3')
  >>> cplone = concepts['plone'] = Concept(u'Plone')
  >>> for c in (czope, czope2, czope3, cplone):
  ...     c.conceptType = topic
  >>> czope.assignChild(czope2)
  >>> czope.assignChild(czope3)
  >>> czope2.assignChild(cplone)
  >>> rplone.assignConcept(cplone)

Now we can fill our search form and execute the query; note that all concepts
found are listed, plus all their children and all resources associated
with them:

  >>> form = {'search.3.type': 'loops:concept:topic', 'search.3.text': u'zope'}
  >>> request = TestRequest(form=form)
  >>> resultsView = SearchResults(page, request)
  >>> results = list(resultsView.results)
  >>> len(results)
  5
  >>> results[0].context.__name__
  u'plone'

  >>> form = {'search.3.type': 'loops:concept:topic', 'search.3.text': u'zope3'}
  >>> request = TestRequest(form=form)
  >>> resultsView = SearchResults(page, request)
  >>> results = list(resultsView.results)
  >>> len(results)
  1
  >>> results[0].context.__name__
  u'zope3'

To support easy entry of concepts to search for we can preselect the available
concepts (optionally restricted to a certain type) by entering text parts
of the concepts' titles:

  >>> form = {'searchType': 'loops:concept:topic', 'searchString': u'zope'}
  >>> request = TestRequest(form=form)
  >>> view = Search(page, request)
  >>> view.listConcepts()
  "[['Zope (Topic)', '12']]"

Preset Concept Types on Search Forms
------------------------------------

Often we want to include certain types in our search. We can instruct
the search form to include lines for these types by giving these types
a certain qualifier, via the option attribute of the type interface.

Let's start with a new type, the customer type.

  >>> customer = concepts['customer'] = Concept('Customer')
  >>> customer.conceptType = typeConcept
  >>> custType = ITypeConcept(customer)
  >>> custType.options
  []

  >>> cust1 = concepts['cust1'] = Concept(u'Zope Corporation')
  >>> cust2 = concepts['cust2'] = Concept(u'cyberconcepts')
  >>> for c in (cust1, cust2): c.conceptType = customer

  >>> from cybertools.typology.interfaces import IType
  >>> IType(cust1).qualifiers
  ('concept',)

  >>> searchView = Search(search, TestRequest())
  >>> list(searchView.presetSearchTypes)
  []

We can now add a 'search' qualifier to the customer type's options
and thus include the customer type in the preset search types.

  >>> custType.options = ('qualifier:search',)
  >>> IType(cust1).qualifiers
  ('concept', 'search')
  >>> searchView = Search(search, TestRequest())
  >>> list(searchView.presetSearchTypes)
  [{'token': 'loops:concept:customer', 'title': 'Customer'}]

  >>> searchView.conceptsForType('loops:concept:customer')
  [{'token': 'none', 'title': u'not selected'},
   {'token': '18', 'title': u'Zope Corporation'},
   {'token': '19', 'title': u'cyberconcepts'}]

Let's use this new search option for querying:

  >>> form = {'search.4.text_selected': u'18'}
  >>> resultsView = SearchResults(page, TestRequest(form=form))
  >>> results = list(resultsView.results)
  >>> results[0].title
  u'Zope Corporation'


Automatic Filtering
-------------------

TODO - more to come...

