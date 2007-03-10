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

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface

and build a simple loops site with a concept manager and some concepts
(with a relation registry, a catalog, and all the type machinery - what
in real life is done via standard ZCML setup):

  >>> from cybertools.relation.tests import IntIdsStub
  >>> component.provideUtility(IntIdsStub())
  >>> from cybertools.relation.registry import RelationRegistry
  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> relations = RelationRegistry()
  >>> relations.setupIndexes()
  >>> component.provideUtility(relations, IRelationRegistry)

  >>> from loops.type import ConceptType, TypeConcept
  >>> component.provideAdapter(ConceptType)
  >>> component.provideAdapter(TypeConcept)

  >>> from zope.app.catalog.catalog import Catalog
  >>> catalog = Catalog()
  >>> from zope.app.catalog.interfaces import ICatalog
  >>> component.provideUtility(catalog, ICatalog)

  >>> from zope.app.catalog.field import FieldIndex
  >>> from zope.app.catalog.text import TextIndex
  >>> from loops.interfaces import IIndexAttributes
  >>> catalog['loops_title'] = TextIndex('title', IIndexAttributes)
  >>> catalog['loops_text'] = TextIndex('text', IIndexAttributes)
  >>> catalog['loops_type'] = TextIndex('type', IIndexAttributes)

  >>> from loops import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.knowledge.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='knowledge')
  >>> from loops.setup import SetupManager
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()

  >>> from loops import util
  >>> from loops.concept import IndexAttributes
  >>> component.provideAdapter(IndexAttributes)

  >>> from loops.concept import Concept

  >>> for c in concepts:
  ...     catalog.index_doc(util.getUidForObject(c), c)

  >>> #sorted(concepts)


Text Queries
============


Fin de partie
=============

  >>> placefulTearDown()

