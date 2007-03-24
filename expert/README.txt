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


Type- and Text-based Queries
============================

  >>> from loops.expert import query
  >>> qu = query.Title('ty*')
  >>> list(qu.apply())
  [0, 1, 41]

  >>> qu = query.Type('loops:*')
  >>> len(list(qu.apply()))
  35

  >>> qu = query.Type('loops:concept:predicate')
  >>> len(list(qu.apply()))
  6

  >>> qu = query.Type('loops:concept:predicate') & query.Title('t*')
  >>> list(qu.apply())
  [1]


Relationship-based Queries
==========================

In addition to the simple methods of concepts and resources for accessing
relations to other objects the expert package provides methods
for selecting and filtering related objects using our basic querying
syntax (that in turn is based on hurry.query).

  >>> stateNew = concepts['new']
  >>> qu = query.Resources(stateNew)
  >>> list(qu.apply())
  [57, 62]


Fin de partie
=============

  >>> placefulTearDown()

