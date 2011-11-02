===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']


Compund Objects - Hierarchies with Ordered Components
=====================================================

  >>> from loops.compound.base import Compound
  >>> component.provideAdapter(Compound)

  >>> tType = concepts.getTypeConcept()
  >>> from loops.setup import addAndConfigureObject
  >>> from loops.concept import Concept
  >>> from loops.compound.interfaces import ICompound

We first create the compound type and one instance of the newly created
type. We also need an ``ispartof`` predicate.

  >>> tCompound = addAndConfigureObject(concepts, Concept, 'compound',
  ...                   title=u'Compound',
  ...                   conceptType=tType, typeInterface=ICompound)
  >>> c01 = addAndConfigureObject(concepts, Concept, 'c01',
  ...                    title=u'Compound #01', conceptType=tCompound)
  >>> tPredicate = concepts.getPredicateType()
  >>> isPartof = addAndConfigureObject(concepts, Concept, 'ispartof',
  ...                   title=u'is Part of', conceptType=tPredicate)

In order to access the compound concept's attributes we have to adapt
it.

  >>> from loops.common import adapted
  >>> aC01 = adapted(c01)

Now we are able to add resources to it.

  >>> aC01.add(resources[u'd003.txt'])
  >>> aC01.add(resources[u'd001.txt'])

  >>> [getName(p) for p in aC01.getParts()]
  [u'd003.txt', u'd001.txt']

  >>> aC01.add(resources[u'd001.txt'], 0)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd001.txt', u'd003.txt', u'd001.txt']

  >>> aC01.add(resources[u'd002.txt'], -1)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd001.txt', u'd003.txt', u'd002.txt', u'd001.txt']

We can reorder the parts of a compound.

  >>> aC01.reorder([resources[u'd002.txt'], resources[u'd001.txt'], ])
  >>> [getName(p) for p in aC01.getParts()]
  [u'd002.txt', u'd001.txt', u'd003.txt', u'd001.txt']

And remove a part from the compound.

  >>> aC01.remove(resources[u'd001.txt'], 1)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd002.txt', u'd003.txt', u'd001.txt']


Blogs
=====

  >>> from loops.compound.blog.post import BlogPost
  >>> from loops.compound.blog.interfaces import IBlogPost
  >>> component.provideAdapter(BlogPost, provides=IBlogPost)

  >>> tBlog = addAndConfigureObject(concepts, Concept, 'blog', title=u'Blog',
  ...                               conceptType=tType)
  >>> tBlogPost = addAndConfigureObject(concepts, Concept, 'blogpost',
  ...                               title=u'Blog Post', conceptType=tType,
  ...                               typeInterface=IBlogPost)

  >>> myBlog = addAndConfigureObject(concepts, Concept, 'myblog', title=u'My Blog',
  ...                               conceptType=tBlog)

  >>> firstPost = addAndConfigureObject(concepts, Concept, 'firstpost',
  ...                               title=u'My first post', conceptType=tBlogPost)

  >>> aFirstPost = adapted(firstPost)
  >>> aFirstPost.date
  >>> aFirstPost.text = u'My first blog post.'
  >>> aFirstPost.text
  u'My first blog post.'
  >>> aFirstPost.creator

Blog and BlogPost views
-----------------------

  >>> from loops.compound.blog.browser import BlogView, BlogPostView
  >>> #from zope.publisher.browser import TestRequest
  >>> from loops.tests.auth import TestRequest

The blog view automatically provides a portlet action for creating
a new post.

  >>> view = BlogView(myBlog, TestRequest())
  >>> for act in view.getActions('portlet'):
  ...     print act.name
  createBlogPost

  >>> view = BlogPostView(firstPost, TestRequest())
  >>> data = view.data

Automatic assignment of a blog post to the personal blog of its owner
---------------------------------------------------------------------

As all the following stuff relies on a blog being assigned to a person
we need the corresponding scaffolding from the loops.organize package.

  >>> from loops.organize.tests import setupUtilitiesAndAdapters
  >>> setupData = setupUtilitiesAndAdapters(loopsRoot)

We also have to set up some components for automatic setting of
security properties upon object creation.

  >>> from loops.security.common import setDefaultSecurity
  >>> component.provideHandler(setDefaultSecurity)
  >>> from loops.compound.blog.security import BlogPostSecuritySetter
  >>> component.provideAdapter(BlogPostSecuritySetter)

Let's start with defining a user (more precisely: a principal)
and a corresponding person.

  >>> auth = setupData.auth
  >>> tPerson = concepts['person']

  >>> userJohn = auth.definePrincipal('users.john', u'John', login='john')
  >>> persJohn = addAndConfigureObject(concepts, Concept, 'person.john',
  ...                   title=u'John Smith', conceptType=tPerson,
  ...                   userId='users.john')

  >>> blogJohn = addAndConfigureObject(concepts, Concept, 'blog.john',
  ...                   title=u'John\'s Blog', conceptType=tBlog)
  >>> persJohn.assignChild(blogJohn)

Let's now login as the newly defined user.

  >>> from loops.tests.auth import login
  >>> login(userJohn)

Let's also provide some general permission settings. These are necessary
as after logging in the permissions of the user will be checked by the
standard checker defined in the test setup.

  >>> grantPermission = setupData.rolePermissions.grantPermissionToRole
  >>> assignRole = setupData.principalRoles.assignRoleToPrincipal

  >>> grantPermission('zope.View', 'zope.Member')
  >>> grantPermission('zope.View', 'loops.Owner')
  >>> grantPermission('zope.ManageContent', 'zope.ContentManager')
  >>> grantPermission('loops.ViewRestricted', 'loops.Owner')

  >>> assignRole('zope.Member', 'users.john')

The automatic assignment of the blog post is done in the form controller
used for creating the blog post.

  >>> home = views['home']
  >>> home.target = myBlog

  >>> from loops.compound.blog.browser import CreateBlogPostForm, CreateBlogPost
  >>> input = {'title': u'John\'s first post', 'text': u'Text of John\'s post',
  ...          'date': '2008-02-02T15:54:11',
  ...          'privateComment': u'John\'s private comment',
  ...          'form.type': '.loops/concepts/blogpost'}
  >>> cbpForm = CreateBlogPostForm(home, TestRequest(form=input))
  >>> cbpController = CreateBlogPost(cbpForm, cbpForm.request)
  >>> cbpController.update()
  False

  >>> posts = blogJohn.getChildren()
  >>> len(posts)
  1
  >>> postJohn0 = posts[0]
  >>> postJohn0.title
  u"John's first post"

  >>> postJohn0Text = adapted(postJohn0.getResources()[0])
  >>> postJohn0Text.data
  u"Text of John's post"


Security
========

We first have to define some checkers that will be invoked when checking access
to attributes.

  >>> from zope.security.checker import Checker, defineChecker
  >>> checker = Checker(dict(title='zope.View', privateComment='loops.ViewRestricted'),
  ...                   dict(title='zope.ManageContent',
  ...                        privateComment='zope.ManageContent'))
  >>> #defineChecker(Concept, checker)
  >>> defineChecker(BlogPost, checker)

  >>> from loops.resource import Resource, TextDocumentAdapter
  >>> checker = Checker(dict(title='zope.View', data='zope.View'),
  ...                   dict(title='zope.ManageContent', data='zope.ManageContent'))
  >>> #defineChecker(Resource, checker)
  >>> defineChecker(TextDocumentAdapter, checker)

Standard security settings for blogs
------------------------------------

TODO...

A personal blog is a blog that is a direct child of a person with
an associated principal (i.e. a user id).

Blog posts in a personal blog can only be created by the owner of the blog.
More generally: A personal blog may receive only blog posts as children
that have the same owner as the blog itself.

A personal blog may only be assigned to other parents by the owner of
the blog.

Standard security settings for blog posts
-----------------------------------------

Blog posts may (only!) be edited by their owner (i.e. only the owner
has the ManageContent permission). (TODO: Also their parent assignments may be
changed only by the owner).

Note that we still are logged-in as user John.

  >>> from zope.security import canAccess, canWrite, checkPermission
  >>> canAccess(postJohn0, 'title')
  True
  >>> canWrite(postJohn0, 'title')
  True

This settings are also valid for children/resources that are assigned
via an `is Part of` relation.

  >>> canAccess(postJohn0Text, 'data')
  True
  >>> canWrite(postJohn0Text, 'data')
  True

The private comment is only visible (and editable, of course) for the
owner of the blog post.

  >>> aPostJohn0 = adapted(postJohn0)
  >>> canAccess(aPostJohn0, 'privateComment')
  True
  >>> canWrite(aPostJohn0, 'privateComment')
  True

So let's now switch to another user. On a global level, Martha also has
the ContentManager role, i.e. she is allowed to edit content objects.
Nevertheless she is not allowed to change John's blog post.

  >>> userMartha = auth.definePrincipal('users.martha', u'Martha', login='martha')
  >>> assignRole('zope.Member', 'users.martha')
  >>> assignRole('zope.ContentManager', 'users.martha')

  >>> login(userMartha)

  >>> canAccess(postJohn0, 'title')
  True
  >>> canWrite(postJohn0, 'title')
  False

  >>> canAccess(postJohn0Text, 'data')
  True
  >>> canWrite(postJohn0Text, 'data')
  False

  >>> canAccess(aPostJohn0, 'privateComment')
  False
  >>> canWrite(aPostJohn0, 'privateComment')
  False

A blog post marked as private is only visible for its owner.

  >>> login(userJohn)
  >>> aPostJohn0.private = True
  >>> canAccess(postJohn0, 'title')
  True
  >>> canAccess(postJohn0Text, 'data')
  True

  >>> login(userMartha)
  >>> canAccess(postJohn0, 'data')
  False
  >>> canAccess(postJohn0Text, 'data')
  False

When we clear the `private` flag the post becomes visible again.

  >>> aPostJohn0.private = False
  >>> canAccess(postJohn0, 'title')
  True
  >>> canAccess(postJohn0Text, 'title')
  True


Micro Articles
==============

  >>> from loops.compound.microart.base import MicroArt
  >>> from loops.compound.microart.interfaces import IMicroArt
  >>> component.provideAdapter(BlogPost, provides=IMicroArt)

  >>> tMicroArt = addAndConfigureObject(concepts, Concept, 'microart',
  ...                                   title=u'MicroArt', conceptType=tType)


Fin de partie
=============

  >>> placefulTearDown()

