===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName

First we set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']


Stateful Objects
================

A simple publishing workflow
----------------------------

Let's start with registering the states definitions and adapters needed.
The states definition (aka 'workflow') is registered as a utility; for
making an object statful we'll use an adapter.

  >>> from cybertools.stateful.interfaces import IStatesDefinition, IStateful
  >>> from cybertools.stateful.publishing import simplePublishing
  >>> component.provideUtility(simplePublishing(), name='loops.simple_publishing')

  >>> from loops.organize.stateful.base import SimplePublishable
  >>> component.provideAdapter(SimplePublishable, name='loops.simple_publishing')

We may now take a document and adapt it to IStateful so that we may
check the document's state and perform transitions to other states.

  >>> doc01 = resources['d001.txt']
  >>> statefulDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='loops.simple_publishing')

  >>> statefulDoc01.state
  'draft'

  >>> statefulDoc01.doTransition('publish')
  >>> statefulDoc01.state
  'published'

Let's check if the state is really stored in the underlying object and
not just kept in the adapter.

  >>> statefulDoc01_x = component.getAdapter(doc01, IStateful,
  ...                                        name='loops.simple_publishing')

  >>> statefulDoc01.state
  'published'


Controlling classification quality
----------------------------------

  >>> from loops.organize.stateful.quality import classificationQuality
  >>> component.provideUtility(classificationQuality(),
  ...                          name='loops.classification_quality')
  >>> from loops.organize.stateful.quality import ClassificationQualityCheckable
  >>> component.provideAdapter(ClassificationQualityCheckable,
  ...                          name='loops.classification_quality')
  >>> from loops.organize.stateful.quality import assign, deassign
  >>> component.provideHandler(assign)
  >>> component.provideHandler(deassign)

  >>> qcheckedDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='loops.classification_quality')
  >>> qcheckedDoc01.state
  'unclassified'

  >>> tCustomer = concepts['customer']
  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject
  >>> c01 = addAndConfigureObject(concepts, Concept, 'c01', conceptType=tCustomer,
  ...                   title='im publishing')
  >>> c02 = addAndConfigureObject(concepts, Concept, 'c02', conceptType=tCustomer,
  ...                   title='DocFive')

  >>> c01.assignResource(doc01)
  >>> qcheckedDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='loops.classification_quality')
  >>> qcheckedDoc01.state
  'classified'

  >>> c02.assignResource(doc01)
  >>> qcheckedDoc01.state
  'classified'

  >>> qcheckedDoc01.doTransition('verify')
  >>> qcheckedDoc01.state
  'verified'

  >>> c02.deassignResource(doc01)
  >>> qcheckedDoc01.state
  'classified'

  >>> c01.deassignResource(doc01)
  >>> qcheckedDoc01.state
  'unclassified'


Fin de partie
=============

  >>> placefulTearDown()
