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

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> len(concepts) + len(resources)
  14


Accessing a Directory in the Filesystem
=======================================

Let's just reuse the settings of cybertools.integrator.

  >>> from cybertools.integrator.tests.test_filesystem import testDir
  >>> from cybertools.integrator.filesystem import ContainerFactory, FileFactory
  >>> component.provideUtility(ContainerFactory(), name='filesystem')
  >>> component.provideUtility(FileFactory(), name='filesystem')

  >>> from loops.integrator.content.base import ExternalAccess
  >>> component.provideAdapter(ExternalAccess)

  >>> from loops.setup import addAndConfigureObject
  >>> from loops.concept import Concept
  >>> from loops.integrator.content.interfaces import IExternalAccess
  >>> typeConcept = concepts.getTypeConcept()
  >>> tExtAccess = addAndConfigureObject(concepts, Concept, 'extaccess',
  ...                   conceptType=typeConcept, typeInterface=IExternalAccess)

  >>> xa01 = addAndConfigureObject(concepts, Concept, 'xa01',
  ...                   conceptType=tExtAccess,
  ...                   providerName='filesystem', baseAddress=testDir)

  >>> from loops.common import adapted
  >>> xa01_ad =adapted(xa01)

  >>> directory = xa01_ad()
  >>> sorted(directory)
  ['index.html', 'sub']


Traversing Content Trees
========================


Fin de partie
=============

  >>> placefulTearDown()
