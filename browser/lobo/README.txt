===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Using the Lobo Blueprint-based Layout Views
===========================================

  >>> from loops.browser.lobo.standard import Layout


Fin de partie
=============

  >>> placefulTearDown()

