===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Managing versions of resources.

  ($Id$)


Setting up a loops Site and Utilities
=====================================

Let's do some basic set up

  >>> from zope import component, interface
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
  24


Version Information
===================

  >>> from loops.versioning.interfaces import IVersionable
  >>> from loops.versioning.versionable import VersionableResource
  >>> component.provideAdapter(VersionableResource)

We can access versioning information for an object by using an IVersionable
adapter on the object.

  >>> d001 = resources['d001.txt']
  >>> vD001 = IVersionable(d001)

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
  >>> vD001.releasedVersion is d001
  True

Now we can create a new version for our document:

  >>> d001v1_1 = vD001.createVersion()
  >>> sorted(resources)

  >>> vD001v1_1 = IVersionable(d001v1_1)
  >>> vD001v1_1.versionId
  '1.2'
