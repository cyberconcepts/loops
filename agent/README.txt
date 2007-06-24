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

  >>> from loops.agent.core import Agent
  >>> agent = Agent()


Scheduling
==========

Configuration (per job)

- schedule, repeating pattern, conditions
- following job(s), e.g. to start a transfer immediately after a crawl

How does this work?
-------------------

  >>> from loops.agent.schedule import Job
  >>> class TestJob(Job):
  ...     def execute(self, **kw):
  ...         d = super(TestJob, self).execute(**kw)
  ...         print 'executing'
  ...         return d

  >>> from time import time
  >>> scheduler = agent.scheduler
  >>> scheduler.schedule(TestJob(), int(time()))

  >>> tester.iterate()
  executing

We can set up a more realistic example using the dummy crawler and transporter
classes from the testing package.

  >>> from loops.agent.testing.crawl import CrawlingJob
  >>> from loops.agent.testing.transport import Transporter, TransportJob

  >>> crawl = CrawlingJob()
  >>> transporter = Transporter()
  >>> transport = TransportJob(transporter)
  >>> crawl.successors.append(transport)
  >>> scheduler.schedule(crawl, int(time()))

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

- URL of the target loops site, e.g. http://z3.loops.cy55.de/bwp/d5
- username, password for logging in to loops
- machine name: name under which the client computer is know to the
  loops server
- Transfer method, e.g. PUT

The following information is intended for the default transfer
protocol/method HTTP PUT but probably also pertains to other protocols
like e.g. FTP.

Format/Information structure
----------------------------

- Metadata URL (for storing or accessing metadata sets - optional, see below):
  ``$loopsSiteURL/resource_meta/$machine_name/$service/$path.xml``
- Resource URL (for storing or accessing the real resources):
  ``$loopsSiteURL/resource_data/$machine_name/$service/$path``
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


Configuration Management
========================

Functionality

- Storage of configuration parameters
- Interface to the browser-based user interface that allows the
  editing of configuration parameters


Browser-based User Interface
============================

The user interface is provided via a browser-based application
based on Twisted and Nevow.

