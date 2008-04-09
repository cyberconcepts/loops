===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Let's do some basic setup

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  >>> from zope import component, interface

and set up a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.organize.tracking.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize.tracking')

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Tracking Changes and Object Access
==================================

  >>> loopsRoot = concepts.getLoopsRoot()
  >>> records = loopsRoot.getRecordManager()
  >>> changes = records['changes']

User management setup
---------------------

In order to be able to login and store personal data
we have to prepare our environment. We need some basic adapter registrations,
and a pluggable authentication utility with a principal folder.

  >>> from loops.organize.tests import setupObjectsForTesting
  >>> setupData = setupObjectsForTesting(site, concepts)
  >>> johnC = setupData.johnC

Recording changes to objects
----------------------------

  >>> from loops.organize.tracking.change import recordModification
  >>> component.provideHandler(recordModification)

  >>> tTask = concepts['task']
  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject
  >>> t01 = addAndConfigureObject(concepts, Concept, 't01', conceptType=tTask,
  ...                   title='Develop change tracking')

  >>> len(changes)
  1


Fin de partie
=============

  >>> placefulTearDown()
