===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

The loops expert - knows what is in a loops site and how to make
use of it.

  ($Id$)

The query stuff depends on hurry.query, see
http://cheeseshop.python.org/pypi/hurry.query


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

  >>> #sorted(concepts)
  >>> #sorted(resources)
  >>> len(concepts) + len(resources)
  35

  >>> #from zope.app.catalog.interfaces import ICatalog
  >>> #sorted(component.getUtility(ICatalog).keys())


Type- and Text-based Queries
============================

  >>> from loops.expert import query
  >>> t = query.Title('ty*')
  >>> list(t.apply())
  [0, 1, 39]

  >>> t = query.Type('loops:*')
  >>> len(list(t.apply()))
  35

  >>> t = query.Type('loops:concept:predicate')
  >>> len(list(t.apply()))
  6

  >>> t = query.Type('loops:concept:predicate') & query.Title('t*')
  >>> list(t.apply())
  [1]


Relationship-based Queries
==========================

In addition to the simple methods of concepts and resources for accessing
relations to other objects the expert package provides methods
for selecting and filtering related objects using our basic querying
syntax (that in turn is based on hurry.query).


Fin de partie
=============

  >>> placefulTearDown()

