===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Managing versions of resources.

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

  >>> from loops.versioning.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> #sorted(concepts)
  >>> #sorted(resources)
  >>> len(concepts) + len(resources)
  23

  >>> loopsRoot = site['loops']
  >>> loopsRoot.options = ['useVersioning']


Version Information
===================

  >>> from loops.versioning.interfaces import IVersionable
  >>> from loops.versioning.versionable import VersionableResource
  >>> component.provideAdapter(VersionableResource)

We can access versioning information for an object by using an IVersionable
adapter on the object.

  >>> d001 = resources['d001.txt']
  >>> d001.title
  u'Doc 001'
  >>> vD001 = IVersionable(d001)
  >>> vD001.versionLevels
  ['major', 'minor']

If there aren't any versions associated with the object we get the default
values:

  >>> vD001.master is d001
  True
  >>> vD001.versionId
  '1.1'
  >>> vD001.versions
  {}
  >>> vD001.currentVersion is d001
  True
  >>> vD001.releasedVersion is None
  True

Now we can create a new version for our document:

  >>> d001v1_2 = vD001.createVersion()
  >>> getName(d001v1_2)
  u'd001_1.2.txt'
  >>> d001v1_2.title
  u'Doc 001'

  >>> vD001v1_2 = IVersionable(d001v1_2)
  >>> vD001v1_2.versionId
  '1.2'

  >>> vD001.currentVersion is d001v1_2
  True
  >>> vD001.master is d001
  True
  >>> vD001v1_2.master is d001
  True

  >>> sorted(vD001.versions)
  ['1.1', '1.2']

When we use a higer level (i.e. a lower number for level) to denote
a major version change, the lower levels are reset to 1:

  >>> d001v2_1 = vD001.createVersion(0)
  >>> getName(d001v2_1)
  u'd001_2.1.txt'

The name of the new version is always derived from the name of the master
even if we create a new version from another one:

  >>> d001v2_2 = IVersionable(d001v1_2).createVersion()
  >>> getName(d001v2_2)
  u'd001_2.2.txt'


Providing the Correct Version
=============================

When accessing resources as targets for view nodes, the node's traversal adapter
(see loops.view.NodeTraverser) uses the versioning framework to retrieve
the correct version of a resource by calling the getVersion() function.

  >>> from loops.versioning.util import getVersion
  >>> from zope.publisher.browser import TestRequest

The default version is always the released or - if this is not available -
the current version (i.e. the version created most recently):

  >>> IVersionable(getVersion(d001, TestRequest())).versionId
  '2.2'

  >>> IVersionable(getVersion(d001v1_2, TestRequest())).versionId
  '2.2'

  >>> d002 = resources['d002.txt']
  >>> IVersionable(getVersion(d002, TestRequest())).versionId
  '1.1'

When using the expression "version=this" as a URL parameter the object
addressed will be returned without looking for a special version:

  >>> IVersionable(getVersion(d001, TestRequest(form=dict(version='this')))).versionId
  '1.1'

In addition it is possible to explicitly retrieve a certain version:

  >>> IVersionable(getVersion(d001v1_2, TestRequest(form=dict(version='1.1')))).versionId
  '1.1'


Deleting Versioned Resources
============================

When a version object is deleted the reference to it on the corresponding
master object is removed.

  >>> del resources['d001_1.2.txt']
  >>> sorted(IVersionable(d001).versions)
  ['1.1', '2.1', '2.2']

When the master object of a versioned resource is deleted all version objects
derived from it are deleted as well.

  >>> del resources['d001.txt']
  >>> sorted(resources)
  [u'd002.txt', u'd003.txt']


Fin de partie
=============

  >>> placefulTearDown()
