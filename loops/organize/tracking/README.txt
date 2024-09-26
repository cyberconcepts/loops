===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

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
  >>> from zope.publisher.browser import TestRequest
  >>> from cybertools.browser.view import BodyRenderedEvent

  >>> loopsRoot.options = [logfile_option + ':test.log']

  >>> request = TestRequest()
  >>> home = views['home']
  >>> record(request, principal='users.john', view='render',
  ...                 node=util.getUidForObject(home),
  ...                 target=util.getUidForObject(resources['d001.txt']),
  ...       )
  >>> logAccess(BodyRenderedEvent(home, request), testDir)

  >>> record(request, principal='users.john', view='render',
  ...                 node=util.getUidForObject(home),
  ...                 target=util.getUidForObject(resources['d002.txt']),
  ...       )
  >>> logAccess(BodyRenderedEvent(home, request), testDir)

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
  'AccessRecordManager: 2 records loaded.'
  >>> len(access)
  2


Tracking Reports
================

Overview (cumulative) statistics
--------------------------------

  >>> from loops.expert.concept import IQueryConcept
  >>> tQuery = concepts['query'] = addAndConfigureObject(concepts, Concept,
  ...                   'query', conceptType=concepts.getTypeConcept(),
  ...                   typeInterface=IQueryConcept)
  >>> statQuery = addAndConfigureObject(concepts, Concept, 'stats',
  ...                   conceptType=tQuery)

  >>> from loops.organize.tracking.report import TrackingStats
  >>> view = TrackingStats(statQuery, TestRequest())
  >>> result = view.getData()
  >>> result['macro'][4][1]['define-macro']
  'overview'
  >>> result['data']
  [{'period': '...', ...}]

[{'access': 2, 'new': 0, 'changed': 1, 'period': '...', 'count': 3}]


Changes for a certain period (month)
------------------------------------

  >>> input = dict(period='2009-01', select='access')
  >>> view = TrackingStats(statQuery, TestRequest(form=input))
  >>> result = view.getData()
  >>> result['data']
  [...]

Recent changes
--------------

  >>> from loops.organize.tracking.report import RecentChanges
  >>> view = RecentChanges(statQuery, TestRequest())
  >>> result = view.getData()
  >>> result['macro'][4][1]['define-macro']
  'recent_changes'

  >>> data = result['data']
  >>> data
  [<ChangeRecord ['27', 2, '33', '...']: {'action': 'modify'}>]

  >>> data[0].timeStamp
  '... ...:...'

  >>> data[0].objectData
  {'object': ...}

{'version': '', 'description': '', 'title': 'Change Doc 001', 'url': '', 
 'object': <loops.resource.Resource object at ...>, 'type': 'Text', 
 'canAccess': True}

  >>> data[0].user
  {'object': ...}

{'url': '', 'object': <loops.concept.Concept ...>, 'title': 'john'}

  >>> data[0].action
  'modify'


Fin de partie
=============

  >>> import os
  >>> for fn in os.listdir(testDir):
  ...     if '.log' in fn:
  ...         os.unlink(os.path.join(testDir, fn))
  >>> placefulTearDown()
