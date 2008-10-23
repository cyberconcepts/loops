===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

loops System Management.

  ($Id$)


Setting up a loops Site and Utilities
=====================================

Let's do some basic set up

  >>> from zope import component, interface
  >>> from zope.traversing.api import getName
  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

and build a simple loops site with a concept manager and some concepts
(with a relation registry, a catalog, and all the type machinery - what
in real life is done via standard ZCML setup or via local utility
configuration):

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> appRoot = site['loops']

In addition to the application site we need a loops system management site.

  >>> from loops.interfaces import ILoops, IConcept
  >>> from loops.setup import ISetupManager
  >>> from loops.system.setup import SetupManager
  >>> component.provideAdapter(SetupManager, (ILoops,), ISetupManager,
  ...                           name='system')

  >>> sysConcepts, sysResources, sysViews = t.siteSetup('loops.system')
  >>> systemRoot = site['loops.system']

  >>> sorted(sysConcepts)
  [u'domain', u'file', u'hasType', u'job', u'note', u'predicate',
   u'standard', u'textdocument', u'type']


Agents and Jobs
===============


Fin de partie
=============

  >>> placefulTearDown()
