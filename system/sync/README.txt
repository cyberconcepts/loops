===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.expert.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']
  >>> len(concepts), len(resources), len(views)
  (30, 3, 1)


Synchronize: Transfer Changes from one loops Site to Another
============================================================

  >>> from loops.system.sync.browser import SyncChanges


Fin de Partie
=============

  >>> placefulTearDown()
