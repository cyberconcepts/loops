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

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']

Let's also set up logging in a way that we get notified about problems.

  >>> import sys
  >>> from logging import getLogger, StreamHandler
  >>> getLogger('loops.organize.job').addHandler(StreamHandler(sys.stdout))


Execute Jobs via a cron Call
============================

  >>> from zope.publisher.browser import TestRequest
  >>> from loops.organize.job.browser import Executor

The executor is a view that will be called by calling its ``processJobs``
method. As we haven't yet defined any job managers nothing happens.

  >>> executor = Executor(loopsRoot, TestRequest())
  >>> executor.processJobs()
  'No job managers available.'

We now register a job manager via an options setting on the loops root object.
As the corresponding job manager is not yet defined an registered a
warning is issued.

  >>> loopsRoot.options = ['organize.job.managers:loops_notifier']
  >>> executor = Executor(loopsRoot, TestRequest())
  >>> r = executor.processJobs()
  Job manager 'loops_notifier' not found.

So let's now define a job manager class and register it as an adapter for
the loops root object.

  >>> from loops.organize.job.base import JobManager
  >>> class Notifier(JobManager):
  ...     def process(self):
  ...         print 'processing...'

  >>> component.provideAdapter(Notifier, name='loops_notifier')
  >>> loopsRoot.options = ['organize.job.managers:loops_notifier']
  >>> executor = Executor(loopsRoot, TestRequest())
  >>> executor.processJobs()
  processing...


Fin de partie
=============

  >>> placefulTearDown()
