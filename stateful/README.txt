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

Let's start with registering the states definitions and adapters needed.
The states definition (aka 'workflow') is registered as a utility; for
making an object statful we'll use an adapter.

  >>> from cybertools.stateful.interfaces import IStatesDefinition, IStateful
  >>> from cybertools.stateful.publishing import simplePublishing
  >>> component.provideUtility(simplePublishing, IStatesDefinition,
  ...                          name='loops.simple_publishing')

  >>> from loops.stateful.base import SimplePublishable
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
