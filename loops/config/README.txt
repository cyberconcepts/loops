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

  >>> opt.organize.tracking
  ['changes', 'access']
  >>> opt.useVersioning
  True

  >>> print(opt)
  useVersioning=True
  organize(tracking=['changes', 'access'])

If we query an option that is not defined on the site level we get a
dummy element that corresponds to False.

  >>> opt.i18n.languages
  <AutoElement 'languages'>
  >>> bool(opt.i18n.languages)
  False

We can use a utility for providing global settings.

  >>> from cybertools.meta.interfaces import IOptions
  >>> globalOpt = component.getUtility(IOptions)
  >>> globalOpt.i18n.languages = ['en', 'de']
  >>> globalOpt.i18n.languages
  ['en', 'de']

If we call the site options with the key we want to query the global
options will be used as a fallback.

  >>> opt('i18n.languages')
  ['en', 'de']

User options (preferences)
--------------------------

Type- and object-based settings
-------------------------------


Configurator User Interface
===========================


Fin de partie
=============

  >>> placefulTearDown()
