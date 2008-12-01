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

  >>> from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
  >>> from zope.event import notify
  >>> resources['d001.txt'].title = 'Change Doc 001'
  >>> notify(ObjectModifiedEvent(resources['d001.txt']))
  >>> len(changes)
  2

Recording assignment changes
----------------------------

  >>> from loops.organize.tracking.change import recordAssignment, recordDeassignment
  >>> component.provideHandler(recordAssignment)
  >>> component.provideHandler(recordDeassignment)

  >>> t01.assignChild(johnC)
  >>> len(changes)
  3


Tracking Object Access
======================

Access records are not directly stored in the ZODB (in order to avoid
conflict errors) but are first stored to a log file.

Even this logging is a two-step process: the data to be logged are first collected
in the request; all collected data are then written triggered by the
EndRequestEvent.

  >>> from loops.organize.tracking.access import logfile_option, record, logAccess
  >>> #from loops.organize.tracking.access import AccessRecordManagerView
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
  >>> logAccess(EndRequestEvent(NodeView(home, request), request), testDir)

  >>> record(request, principal='users.john', view='render',
  ...                 node=util.getUidForObject(home),
  ...                 target=util.getUidForObject(resources['d002.txt']),
  ...       )
  >>> logAccess(EndRequestEvent(NodeView(home, request), request), testDir)

The access log can then be read in via an AccessRecordManager object, i.e. a view
that may be called via ``wget`` using a crontab entry or some other kind
of job control.

  >>> access = records['access']
  >>> len(access)
  0

  >>> #rm = AccessRecordManagerView(loopsRoot, TestRequest())
  >>> rm = AccessRecordManager(loopsRoot)
  >>> rm.baseDir = testDir
  >>> rm.loadRecordsFromLog()
  >>> len(access)
  2


Tracking Reports
================

  >>> from loops.organize.tracking.report import TrackingStats

  >>> view = TrackingStats(home, TestRequest())
  >>> result = view.getData()
  >>> result['macro'][4][1][u'define-macro']
  u'overview'
  >>> result['data']
  [{'access': 2, 'new': 0, 'changed': 1, 'period': '...', 'count': 3}]


Fin de partie
=============

  >>> import os
  >>> for fn in os.listdir(testDir):
  ...     if '.log' in fn:
  ...         os.unlink(os.path.join(testDir, fn))
  >>> placefulTearDown()
