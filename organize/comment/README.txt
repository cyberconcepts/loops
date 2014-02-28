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

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Comments - Managed by a Tracking Storage
========================================

  >>> loopsRoot = concepts.getLoopsRoot()
  >>> records = loopsRoot.getRecordManager()

More setup
----------

In order to be able to login and store favorites and other personal data
we have to prepare our environment. We need some basic adapter registrations,
and a pluggable authentication utility with a principal folder.

  >>> from loops.organize.tests import setupObjectsForTesting
  >>> setupData = setupObjectsForTesting(site, concepts)
  >>> johnC = setupData.johnC

We also assign a document as a target to the home node so that we are able
to assign comments to this document.

  >>> home = views['home']
  >>> home.target = resources['d001.txt']

  >>> from loops.organize.comment.base import commentStates
  >>> component.provideUtility(commentStates(), name='organize.commentStates')

Creating comments
-----------------

  >>> from loops.browser.node import NodeView
  >>> from loops.tests.auth import TestRequest
  >>> view = NodeView(home, TestRequest())

  >>> from loops.organize.comment.browser import CreateComment

  >>> input = dict(subject='My comment', text='Comment text')
  >>> fc = CreateComment(view, TestRequest(form=input))
  >>> fc.update()
  False


Viewing comments
----------------

  >>> from loops.organize.comment.browser import CommentsView
  >>> comments = CommentsView(home, TestRequest())

  >>> items = list(comments.allItems())
  >>> items
  [<Comment ['27', 1, '33', '... ...']:
    {'text': 'Comment text', 'subject': 'My comment'}>]
  >>> item = items[0]
  >>> item.subject, item.timeStamp, item.user['title']
  ('My comment', u'... ...', u'john')


Fin de partie
=============

  >>> placefulTearDown()
