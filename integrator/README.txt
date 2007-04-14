===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Integration of external sources.

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

  >>> from loops.integrator.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> len(concepts) + len(resources)
  18


External Collections
====================

The basis of our work will be ExternalCollection objects, i.e. concepts
of the 'extcollection' type. We use an adapter for providing the attributes
and methods of the external collect object.

  >>> from loops.concept import Concept
  >>> from loops.setup import addObject
  >>> from loops.integrator.collection import ExternalCollectionAdapter
  >>> tExternalCollection = concepts['extcollection']
  >>> coll01 = addObject(concepts, Concept, 'coll01',
  ...                    title=u'Collection One', conceptType=tExternalCollection)
  >>> aColl01 = ExternalCollectionAdapter(coll01)

An external collection carries a set of attributes that control the access
to the external system:

  >>> aColl01.providerName, aColl01.baseAddress, aColl01.address, aColl01.pattern
  (None, None, None, None)
  >>> from loops.integrator.testsetup import dataDir
  >>> aColl01.baseAddress = dataDir
  >>> aColl01.address = 'topics'


Directory Collection Provider
-----------------------------

The DirectoryCollectionProvider collects files from a directory in the
file system. The parameters (directory paths) are provided by the calling
object, the external collection itself.

  >>> from loops.integrator.collection import DirectoryCollectionProvider
  >>> dcp = DirectoryCollectionProvider()

  >>> sorted(dcp.collect(aColl01))
  ['programming/BeautifulProgram.pdf', 'programming/zope/zope3.txt']

If we provide a selective pattern we get only part of the files:

  >>> aColl01.pattern = r'.*\.txt'
  >>> sorted(dcp.collect(aColl01))
  ['programming/zope/zope3.txt']

Let's now create the corresponding resource objects.

  >>> aColl01.pattern = ''
  >>> addresses = dcp.collect(aColl01)
  >>> res = list(dcp.createExtFileObjects(aColl01, addresses))
  >>> len(sorted(r.__name__ for r in res))
  2
  >>> xf1 = res[0]
  >>> xf1.__name__
  u'programming/BeautifulProgram.pdf'


Fin de partie
=============

  >>> placefulTearDown()
