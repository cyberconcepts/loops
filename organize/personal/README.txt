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

  >>> from loops.organize.tests import setupUtilitiesAndAdapters
  >>> setupData = setupUtilitiesAndAdapters(loopsRoot)

  >>> from zope.app.appsetup.bootstrap import ensureUtility
  >>> from zope.app.authentication.authentication import PluggableAuthentication
  >>> from zope.app.security.interfaces import IAuthentication
  >>> ensureUtility(site, IAuthentication, '', PluggableAuthentication,
  ...               copy_to_zlog=False, asObject=True)
  <...PluggableAuthentication...>
  >>> pau = component.getUtility(IAuthentication, context=site)

  >>> from zope.app.authentication.principalfolder import PrincipalFolder
  >>> from zope.app.authentication.interfaces import IAuthenticatorPlugin
  >>> pFolder = PrincipalFolder('users.')
  >>> pau['users'] = pFolder
  >>> pau.authenticatorPlugins = ('users',)

So we can now register a user ...

  >>> from zope.app.authentication.principalfolder import InternalPrincipal
  >>> pFolder['john'] = InternalPrincipal('john', 'xx', u'John')
  >>> from zope.app.authentication.principalfolder import FoundPrincipalFactory
  >>> component.provideAdapter(FoundPrincipalFactory)

... and create a corresponding person.

  >>> from loops.concept import Concept
  >>> johnC = concepts['john'] = Concept(u'John')
  >>> person = concepts['person']
  >>> johnC.conceptType = person
  >>> from loops.common import adapted
  >>> adapted(johnC).userId = 'users.john'

Finally, we log in as the newly created user.

  >>> from zope.app.authentication.principalfolder import Principal
  >>> pJohn = Principal('users.john', 'xxx', u'John')

  >>> from loops.tests.auth import login
  >>> login(pJohn)

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

(We always need a "run" - can we try to ignore this for favorites?)

  >>> runId = favorites.startRun()

For favorites we don't need any data...

  >>> favorites.saveUserTrack(d001Id, runId, johnCId, {})
  '0000001'
  >>> favorites.saveUserTrack(d003Id, runId, johnCId, {})
  '0000002'

So we are now ready to query the favorites.

  >>> favs = favorites.query(userName=johnCId)
  >>> favs
  [<Favorite ['27', 1, '33', '...']: {}>,
   <Favorite ['31', 1, '33', '...']: {}>]

  >>> util.getObjectForUid(favs[0].taskId) is resources['d001.txt']
  True

User interface
--------------

