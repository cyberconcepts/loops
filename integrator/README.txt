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
  17


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
  [('programming/BeautifulProgram.pdf', datetime.datetime(...)),
   ('programming/zope/zope3.txt', datetime.datetime(...))]

If we provide a more selective pattern we get only part of the files:

  >>> aColl01.pattern = r'.*\.txt'
  >>> sorted(dcp.collect(aColl01))
  [('programming/zope/zope3.txt', datetime.datetime(...))]

Let's now create the corresponding resource objects.

  >>> aColl01.pattern = ''
  >>> addresses = [e[0] for e in dcp.collect(aColl01)]
  >>> res = list(dcp.createExtFileObjects(aColl01, addresses))
  >>> len(sorted(r.__name__ for r in res))
  2
  >>> xf1 = res[0]
  >>> xf1.__name__
  u'programming_beautifulprogram.pdf'
  >>> xf1.title
  u'BeautifulProgram'
  >>> xf1.contentType
  'application/pdf'

  >>> from loops.common import adapted
  >>> aXf1 = adapted(xf1)
  >>> aXf1.storageName
  'fullpath'
  >>> aXf1.storageParams
  {'subdirectory': '...topics'}

  >>> for r in res: del resources[r.__name__]

Working with the External Collection
------------------------------------

  >>> component.provideUtility(DirectoryCollectionProvider())
  >>> aColl01.update()
  >>> res = coll01.getResources()
  >>> len(res)
  2
  >>> sorted((r.__name__, r.title, r._storageName) for r in res)
  [(u'programming_beautifulprogram.pdf', u'BeautifulProgram', 'fullpath'),
   (u'programming_zope_zope3.txt', u'zope3', 'fullpath')]

We may update the collection after having changed the storage params.
This should also change the settings for existing objects if they still
can be found.

  >>> import os
  >>> aColl01.address = os.path.join('topics', 'programming')
  >>> aColl01.update()
  >>> res = sorted(coll01.getResources(), key=lambda x: getName(x))
  >>> len(res)
  2
  >>> aXf1 = adapted(res[0])
  >>> aXf1.storageName, aXf1.storageParams, aXf1.externalAddress
  ('fullpath', {'subdirectory': '...programming'}, 'BeautifulProgram.pdf')

But if one of the referenced objects is not found any more it will be deleted.

  >>> aColl01.address = os.path.join('topics', 'programming', 'zope')
  >>> aColl01.update()
  >>> res = sorted(coll01.getResources(), key=lambda x: getName(x))
  >>> len(res)
  1
  >>> aXf1 = adapted(res[0])
  >>> aXf1.storageName, aXf1.storageParams, aXf1.externalAddress
  ('fullpath', {'subdirectory': '...zope'}, 'zope3.txt')


Uploading Resources with HTTP PUT Requests
==========================================

  >>> from zope.publisher.browser import TestRequest
  >>> from zope.traversing.api import getName
  >>> from loops.integrator.put import ResourceManagerTraverser
  >>> from loops.integrator.source import ExternalSourceInfo
  >>> component.provideAdapter(ExternalSourceInfo)

  >>> rrinfo = 'local/user/filesystem'
  >>> rrpath = 'testing/data/file1.txt'
  >>> rrid = '/'.join((rrinfo, rrpath))

  >>> baseUrl = 'http://127.0.0.1/loops/resources'
  >>> url = '/'.join((baseUrl, '.data', rrid))

  >>> request = TestRequest(url)
  >>> request.method = 'PUT'
  >>> request._traversal_stack = list(reversed(rrid.split('/')))

  >>> traverser = ResourceManagerTraverser(resources, request)
  >>> resource = traverser.publishTraverse(request, '.data')
  *** resources.PUT .data local/user/filesystem/testing/data/file1.txt

  >>> getName(resource)
  u'local_user_filesystem_testing_data_file1.txt'
  >>> resource.title
  u'file1'


Fin de partie
=============

  >>> placefulTearDown()
