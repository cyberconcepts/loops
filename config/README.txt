===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Management of configuration settings and preferences.

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


Options Adapters
================

Global and site options
-----------------------

  >>> from loops.config.base import LoopsOptions
  >>> component.provideAdapter(LoopsOptions)

  >>> from cybertools.meta.interfaces import IOptions
  >>> opt = IOptions(loopsRoot)
  >>> opt
  <loops.config.base.LoopsOptions object ...>
  >>> str(opt)
  ''

We now use the loops root object's options field to define
some options.

  >>> loopsRoot.options = ['useVersioning', 'organize.tracking:changes, access']
  >>> opt = IOptions(loopsRoot)
  >>> print opt
  organize(tracking=['changes', 'access'])
  useVersioning=True

  >>> opt.organize.tracking
  ['changes', 'access']
  >>> opt.useVersioning
  True

If we query an option that is not defined on the site level we get a
dummy element that corresponds to False.

  >>> opt.i18n.languages
  <AutoElement 'languages'>
  >>> bool(opt.i18n.languages)
  False


Fin de partie
=============

  >>> placefulTearDown()
