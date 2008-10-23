===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

The loops expert - knows what is in a loops site and how to make
use of it.

  ($Id$)


Setting up a loops Site and Utilities
=====================================

Let's do some basic set up

  >>> from zope import component, interface
  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

and build a simple loops site with a concept manager and some concepts
(with a relation registry, a catalog, and all the type machinery - what
in real life is done via standard ZCML setup or via local utility
configuration):

  >>> from loops.expert.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> len(concepts) + len(resources)
  33

  >>> loopsRoot = site['loops']


Queries
=======

Queries search the loops database (typically but not necessarily the
catalog) for objects fulfilling the criteria given. A query returns
a set of integer UIDs; thus the results of a query may be efficiently combined
with those of other queries using logical operations.


Type- and text-based queries
----------------------------

  >>> from loops.expert import query
  >>> qu = query.Title('ty*')
  >>> list(qu.apply())
  [0, 1, 47]

  >>> qu = query.Type('loops:*')
  >>> len(list(qu.apply()))
  33

  >>> qu = query.Type('loops:concept:predicate')
  >>> len(list(qu.apply()))
  7

  >>> qu = query.Type('loops:concept:predicate') & query.Title('t*')
  >>> list(qu.apply())
  [1, 43]

State-based queries
-------------------

For selecting objects by their state their is a special query with two
arguments, the name of the states definition and the state to search for.
As we have not yet set up any states definitions for our objects we get
an empty result.

  >>> qu = query.State('classification_quality', 'classified')
  >>> list(qu.apply())
  []

Let's now set up the ``classication quality`` states definition with the
corresponding adapter and activate it for the current loops site.

  >>> from loops.organize.stateful.quality import classificationQuality
  >>> component.provideUtility(classificationQuality(),
  ...                          name='classification_quality')
  >>> from loops.organize.stateful.quality import ClassificationQualityCheckable
  >>> component.provideAdapter(ClassificationQualityCheckable,
  ...                          name='classification_quality')

  >>> loopsRoot.options = ['organize.stateful.resource:classification_quality']

We have now to reindex all documents so that the state index gets populated
according to the new settings.

  >>> from zope.app.catalog.interfaces import ICatalog
  >>> catalog = component.getUtility(ICatalog)
  >>> from loops import util
  >>> for r in resources.values():
  ...     catalog.index_doc(int(util.getUidForObject(r)), r)

Now the three documents we are working with are shown as classified (as
they have at least one concept assigned).

  >>> qu = query.State('classification_quality', 'classified')
  >>> list(qu.apply())
  [21, 23, 25]

Using the stateful adapter for a resource we now manually execute the
``verify`` transition.

  >>> from cybertools.stateful.interfaces import IStateful
  >>> statefulD001 = component.getAdapter(resources['d001.txt'], IStateful,
  ...                                     name='classification_quality')
  >>> statefulD001.doTransition('verify')

Now only two resources are still in the ``qualified`` state, the changed
one being in the ``verified`` state.

  >>> list(qu.apply())
  [23, 25]
  >>> qu = query.State('classification_quality', 'verified')
  >>> list(qu.apply())
  [21]

We may also provide a sequence of states for querying.

  >>> qu = query.State('classification_quality', ('classified', 'verified',))
  >>> list(qu.apply())
  [21, 23, 25]

Relationship-based queries
--------------------------

In addition to the simple methods of concepts and resources for accessing
relations to other objects the expert package provides methods
for selecting and filtering related objects using our basic querying
syntax (that in turn is based on hurry.query).

  >>> cust1 = concepts['cust1']
  >>> qu = query.Resources(cust1)
  >>> list(qu.apply())
  [21, 25]

Getting objects
---------------

When a query (or a combination of query terms) has been applied we
want to get at the objects resulting from the query.

The ``getObjects()`` function returns an iterable with the objects.
If the ``root`` argument is supplied only objects belonging to the
corresponding loops site are returned. In addition a ``checkPermission``
argument may be supplied with a function that should be checked for
filtering the results; this defaults to ``canListObjects``.

  >>> from loops.expert.query import getObjects
  >>> objs = getObjects(query.Title('ty*').apply(), root=loopsRoot)
  >>> sorted(o.title for o in objs)
  [u'Document Type', u'Type', u'has Type']


Filters
=======

Basically there are two kinds of filters: One is in fact just a query
term that is joined ``and`` (``&``) operation to another query;
the other one is applied to the objects resulting from applying a
query by checking certain attributes or other conditions, thus reducing
the number of the resulting objects.

Which kind of filtering will be used depends on the implementation - this
may be an efficiency issue; there are also filters that don't have an
equivalent query.

Example 1: "My Items"
---------------------

Let's assume that jim is the person that corresponds to the logged-in user.
We now want to set up a filter that lets pass only objects (resources and
concepts) that are direct or indirect children of jim.

  >>> jim = concepts['jim']

  >>> qu = query.Type('loops:resource:textdocument')
  >>> objs = getObjects(qu.apply())
  >>> sorted(o.title for o in objs)
  [u'Doc 001', u'Doc 002', u'Doc 003']

  >>> from loops.expert import filter
  >>> fltr = filter.Children(jim, recursive=True, includeResources=True)
  >>> sorted(o.title for o in getObjects((qu & fltr.query()).apply()))
  [u'Doc 001', u'Doc 003']

  >>> #fltr.check(concepts['d001.txt'])
  >>> #fltr.check(concepts['d002.txt'])
  >>> #objs = fltr.apply(objs)
  >>> #sorted(o.title for o in objs.values())


Organizing Queries and Filters with Query Instances
===================================================

A query instance consists of

- a base query (a composition of terms)
- one or more query filters that will be joined with the base query
- a result filter that will be applied to the result set of the
  preceding steps

  >>> from loops.expert.instance import QueryInstance
  >>> qi = QueryInstance(qu, fltr)
  >>> #qi.apply()


Query Concepts and Query Views
==============================

  >>> from loops.expert.concept import QueryConcept
  >>> component.provideAdapter(QueryConcept)

  >>> from loops.expert.browser.base import BaseQueryView


Fin de partie
=============

  >>> placefulTearDown()

