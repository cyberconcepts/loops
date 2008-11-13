===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Let's do some basic setup

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  >>> from zope import component, interface

and set up a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.organize.personal.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize.personal')

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Favorites - Managed by a Tracking Storage
=========================================

  >>> loopsRoot = concepts.getLoopsRoot()
  >>> records = loopsRoot.getRecordManager()
  >>> favorites = records['favorites']

User management setup
---------------------

In order to be able to login and store favorites and other personal data
we have to prepare our environment. We need some basic adapter registrations,
and a pluggable authentication utility with a principal folder.

  >>> from loops.organize.tests import setupObjectsForTesting
  >>> setupData = setupObjectsForTesting(site, concepts)
  >>> johnC = setupData.johnC

Working with the favorites storage
----------------------------------

The setup has provided us with a few resources, so there are objects we
can remember as favorites.

  >>> list(resources.keys())
  [u'd001.txt', u'd002.txt', u'd003.txt']

  >>> from loops import util
  >>> d001Id = util.getUidForObject(resources['d001.txt'])
  >>> d003Id = util.getUidForObject(resources['d003.txt'])
  >>> johnCId = util.getUidForObject(johnC)

We do not access the favorites storage directly but by using an adapter.

  >>> from loops.organize.personal.favorite import Favorites
  >>> component.provideAdapter(Favorites)
  >>> from loops.organize.personal.interfaces import IFavorites
  >>> favAdapted = IFavorites(favorites)

The adapter provides convenience methods for accessing the favorites storage.

  >>> favAdapted.add(resources['d001.txt'], johnC)
  '0000001'

So we are now ready to query the favorites.

  >>> favs = list(favorites.query(userName=johnCId))
  >>> favs
  [<Favorite ['27', 1, '33', '...']: {}>]

  >>> list(favAdapted.list(johnC))
  ['27']

  >>> util.getObjectForUid(favs[0].taskId) is resources['d001.txt']
  True

User interface
--------------

  >>> home = views['home']
  >>> from loops.tests.auth import TestRequest
  >>> from loops.organize.personal.browser.configurator import PortletConfigurator

  >>> portletConf = PortletConfigurator(home, TestRequest())
  >>> len(portletConf.viewProperties)
  1

  >>> from loops.organize.personal.browser.favorite import FavoriteView
  >>> view = FavoriteView(home, TestRequest())

Let's now trigger the saving of a favorite.

  >>> d002Id = util.getUidForObject(resources['d002.txt'])
  >>> request = TestRequest(form=dict(id=d002Id))
  >>> view = FavoriteView(home, request)

  >>> view.add()

  >>> len(list(favorites.query(userName=johnCId)))
  2

  >>> d002Id = util.getUidForObject(resources['d001.txt'])
  >>> request = TestRequest(form=dict(id=d002Id))
  >>> view = FavoriteView(home, request)
  >>> view.remove()

  >>> len(list(favorites.query(userName=johnCId)))
  1


Fin de partie
=============

  >>> placefulTearDown()
