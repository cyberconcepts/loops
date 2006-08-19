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

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations, IRelationRegistry)

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
  >>> query = concepts['query'] = Concept(u'Query')
  >>> topic = concepts['topic'] = Concept(u'Topic')
  >>> for c in (query, topic): c.conceptType = typeConcept

In addition we create a concept that holds the search page and a node
(page) that links to this concept:

  >>> search = concepts['search'] = Concept(u'Search')
  >>> search.conceptType = query

  >>> from loops.view import Node
  >>> page = views['page'] = Node('Search Page')
  >>> page.target = search

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
       "http://127.0.0.1/loops/views/page/.target19/@@searchresults.html")'

The searchresults.html view, i.e. the SearchResults view class provides the
result set of the search via its `results` property.

  >>> from loops.search.browser import SearchResults
  >>> form = {'search.2.title': 'yes', 'search.2.text': u'foo' }
  >>> request = TestRequest(form=form)
  >>> resultsView = SearchResults(page, request)

Before accessing the `results` property we have to prepare a catalog.

  >>> from zope.app.catalog.interfaces import ICatalog
  >>> class DummyCat(object):
  ...     implements(ICatalog)
  ...     def searchResults(self, **criteria):
  ...         return []
  >>> component.provideUtility(DummyCat())

  >>> list(resultsView.results)
  []
