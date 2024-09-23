===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Layout management.

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
  >>> loopsRoot = concepts.getLoopsRoot()

  >>> from loops.layout.tests import setup
  >>> setup()


Defining Layouts
================

  >>> from loops.layout.base import LayoutNode

  >>> demo = views['demo'] = LayoutNode('Demo Root Layout')
  >>> demo.nodeType = 'menu'


Fin de partie
=============

  >>> placefulTearDown()
