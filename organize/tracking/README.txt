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


Tracking Changes
================

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

  >>> loopsRoot.options = ['organize.tracking.changes']

  >>> tTask = concepts['task']
  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject
  >>> t01 = addAndConfigureObject(concepts, Concept, 't01', conceptType=tTask,
  ...                   title='Develop change tracking')

  >>> len(changes)
  1

Recording assignment changes
----------------------------

  >>> from loops.organize.tracking.change import recordAssignment, recordDeassignment
  >>> component.provideHandler(recordAssignment)
  >>> component.provideHandler(recordDeassignment)

  >>> t01.assignChild(johnC)
  >>> len(changes)
  2


Tracking Object Access
======================

Access records are not directly stored in the ZODB (in order to avoid
conflict errors) but first stored to a log file.

  >>> from loops.organize.tracking.access import logfile_option, record, logAccess
  >>> from loops.organize.tracking.access import AccessRecordManager
  >>> from loops.organize.tracking.tests import testDir
  >>> from loops.browser.node import NodeView
  >>> from loops.browser.resource import ResourceView
  >>> from loops import util
  >>> from zope.app.publication.interfaces import EndRequestEvent
  >>> from zope.publisher.browser import TestRequest

  >>> loopsRoot.options = [logfile_option + ':test.log']

  >>> request = TestRequest()
  >>> home = views['home']
  >>> record(request, principal='users.john', view='render',
  ...                 node=util.getUidForObject(home),
  ...                 target=util.getUidForObject(resources['d001.txt']),
  ...       )
  >>> record(request, principal='users.john', view='render',
  ...                 node=util.getUidForObject(home),
  ...                 target=util.getUidForObject(resources['d002.txt']),
  ...       )

  >>> logAccess(EndRequestEvent(NodeView(home, request), request), testDir)

They can then be read in via an AccessRecordManager object, i.e. a view
that may be called via ``wget`` using a crontab entry or some other kind
of job control.

  >>> rm = AccessRecordManager(loopsRoot, TestRequest())
  >>> rm.baseDir = testDir
  >>> rm.loadRecordsFromLog()


Fin de partie
=============

  >>> import os
  >>> for fn in os.listdir(testDir):
  ...     if '.log' in fn:
  ...         os.unlink(os.path.join(testDir, fn))
  >>> placefulTearDown()
