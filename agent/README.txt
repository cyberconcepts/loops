===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

loops agents - running on client systems and other services,
collecting informations and transferring them to the loops server.

  ($Id$)

This package does not depend on zope or the other loops packages
but represents a standalone application.

But we need a reactor for working with Twisted; in order not to block
testing when running the reactor we use reactor.iterate() calls
wrapped in a ``tester`` object.

  >>> from loops.agent.tests import tester


Basic Implementation, Agent Core
================================

The agent uses Twisted's cooperative multitasking model.

This means that all calls to services (like crawler, transporter, ...)
return a deferred that must be supplied with a callback method (and in
most cases also an errback method).

  >>> from loops.agent import core
  >>> agent = core.Agent()


Configuration Management
========================

Functionality

- Storage of configuration parameters
- Interface to the browser-based user interface that allows the
  editing of configuration parameters

All configuration parameters are always accessible via the ``config``
attribute of the agent object.

  >>> config = agent.config

This already provides all needed sections (transport, crawl, ui), so
we can directly put information into these sections by loading a
string with the corresponding assignment.

  >>> config.load('transport.url = "http://loops.cy55.de"')
  >>> config.transport.url
  'http://loops.cy55.de'

This setting may also contain indexed access; thus we can model
configuration parameters with multiple instances (like crawling
jobs).

  >>> config.load('''
  ... crawl[0].type = "filesystem"
  ... crawl[0].directory = "documents/projects"
  ... ''')
  >>> config.crawl[0].type
  'filesystem'
  >>> config.crawl[0].directory
  'documents/projects'

Subsections are created automatically when they are first accessed.

  >>> config.load('ui.web.port = 8081')
  >>> config.ui.web.port
  8081

The ``setdefault()`` method allows to retrieve a value and set
it with a default if not found, in one statement.

  >>> config.ui.web.setdefault('port', 8080)
  8081
  >>> config.transport.setdefault('user', 'loops')
  'loops'

  >>> sorted(config.transport.items())
  [('url', 'http://loops.cy55.de'), ('user', 'loops')]

We can output a configuration in a form that is ready for loading
just by converting it to a string representation.

  >>> print config
  crawl[0].directory = 'documents/projects'
  crawl[0].type = 'filesystem'
  transport.url = 'http://loops.cy55.de'
  transport.user = 'loops'
  ui.web.port = 8081

The configuration may also be saved to a file -
for testing purposes let's use the loops.agent package directory
for storage; normally it would be stored in the users home directory.

  >>> import os
  >>> os.environ['HOME'] = os.path.dirname(core.__file__)

  >>> config.save()

  >>> fn = config.getDefaultConfigFile()
  >>> fn
  '....loops.agent.cfg'

  >>> print open(fn).read()
  crawl[0].directory = 'documents/projects'
  crawl[0].type = 'filesystem'
  transport.url = 'http://loops.cy55.de'
  transport.user = 'loops'
  ui.web.port = 8081

Cleaning up up...

  >>> os.unlink(fn)


Scheduling
==========

Configuration (per job)

- schedule, repeating pattern, conditions
- following job(s), e.g. to start a transfer immediately after a crawl

How does this work?
-------------------

  >>> from loops.agent.schedule import Job
  >>> class TestJob(Job):
  ...     def execute(self):
  ...         d = super(TestJob, self).execute()
  ...         print 'executing'
  ...         return d

  >>> from time import time
  >>> scheduler = agent.scheduler
  >>> scheduler.schedule(TestJob(), int(time()))

  >>> tester.iterate()
  executing

We can set up a more realistic example using the dummy crawler and transporter
classes from the testing package.

  >>> from loops.agent.testing import crawl
  >>> from loops.agent.testing import transport

  >>> crawlJob = crawl.CrawlingJob()
  >>> transporter = transport.Transporter(agent)
  >>> transportJob = transporter.jobFactory(transporter)
  >>> crawlJob.successors.append(transportJob)
  >>> scheduler.schedule(crawlJob, int(time()))

  >>> tester.iterate()
  Transferring: Dummy resource data for testing purposes.

Using configuration with scheduling
-----------------------------------

Let's start with a fresh agent, directly supplying the configuration
(just for testing).

  >>> config = '''
  ... crawl[0].type = 'dummy'
  ... crawl[0].directory = '~/documents'
  ... crawl[0].pattern = '.*\.doc'
  ... crawl[0].starttime = %s
  ... crawl[0].transport = 'dummy'
  ... crawl[0].repeat = 0
  ... transport.url = 'http://loops.cy55.de'
  ... ''' % int(time())

  >>> agent = core.Agent(config)

We also register our dummy crawling job and transporter classes as
we can not perform real crawling and transfers when testing.

  >>> agent.crawlTypes = dict(dummy=crawl.CrawlingJob)
  >>> agent.transportTypes = dict(dummy=transport.Transporter)

  >>> agent.scheduleJobsFromConfig()

  >>> tester.iterate()
  Transferring: Dummy resource data for testing purposes.


Crawling
========

General
-------

Functionality

- search for new or changed resources according to the search and
  filter criteria
- keep a record of resources transferred already in order to avoid
  duplicate transfers (?)

Configuration (per crawl job)

- predefined metadata

Local File System
-----------------

Configuration (per crawl job)

- directories to search
- filter criteria, e.g. file type

Metadata sources

- path, filename

E-Mail-Clients
--------------

Configuration (per crawl job)

- folders to search
- filter criteria (e.g. sender, receiver, subject patterns)

Metadata sources

- folder names (path)
- header fields (sender, receiver, subject, ...)

Special handling

- HTML vs. plain text content: if a mail contains both HTML and plain
  text parts the transfer may be limited to one of these parts (configuration
  setting)
- attachments may be ignored (configuration setting; useful when attachments
  are copied to the local filesystem and transferred from there anyways)


Transport
=========

Configuration

- ``transport.url``: URL of the target loops site, e.g.
  "http://z3.loops.cy55.de/bwp/d5"
- ``transport.user``, ``transport.password`` for logging in to loops
- ``transport.machine: name under which the client computer is
  known to the loops server
- ``transport.method``, e.g. "put"

The following information is intended for the default transfer
protocol/method HTTP PUT but probably also pertains to other protocols
like e.g. FTP.

Format/Information structure
----------------------------

- Metadata URL (for storing or accessing metadata sets - optional, see below):
  ``$loopsSiteURL/resource_meta/$machine_name/$user/$service/$path.xml``
- Resource URL (for storing or accessing the real resources):
  ``$loopsSiteURL/resource_data/$machine_name//$user/$service/$path``
- ``$service`` names the crawler service, e.g. "filesystem" or "outlook"
- ``$path`` represents the full path, possibly with drive specification in front
  (for filesystem resources on Windows), with special characters URL-escaped

Note that the URL uniquely identifies the resource on the local computer,
so a resource transferred with the exact location (path and filename)
on the local computer as a resource transferred previously will overwrite
the old version, so that the classification of the resource within loops
won't get lost. (This is of no relevance to emails.)

Metadata sets are XML files with metadata for the associated resource.
Usually a metadata set has the extension ".xml"; if the extension is ".zip"
the metadata file is a compressed file that will be expanded on the
server.

Data files may also be compressed in which case there must be a corresponding
entry in the associated metadata set.


Logging
=======

Configuration

- log format(s)
- log file(s) (or other forms of persistence)


Software Loader
===============

Configuration (general)

- source list: URL(s) of site(s) providing updated or additional packages

Configuration (per install/update job)

- command: install, update, remove
- package names


Browser-based User Interface
============================

The user interface is provided via a browser-based application
based on Twisted and Nevow.

