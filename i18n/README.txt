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

  >>> from loops.interfaces import ILoops, IConcept
  >>> from loops.concept import Concept
  >>> from loops.setup import ISetupManager
  >>> from loops.knowledge.setup import SetupManager
  >>> component.provideAdapter(SetupManager, (ILoops,), ISetupManager,
  ...                           name='knowledge')

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']

  >>> from loops.knowledge.knowledge import Topic
  >>> component.provideAdapter(Topic)

For testing and demonstration purposes let's create a topic.

  >>> topic = concepts['topic']
  >>> topic01 = concepts['topic01'] = Concept(u'loops for Zope 3')
  >>> topic01.conceptType = topic


Content Internationalization
============================

Let's look at a certain concept that should contain i18n-alized data.

  >>> topic01.title
  u'loops for Zope 3'

We can query the available languages, the current language setting and
the default language using a LanguageInfo object that is similar to a view.

  >>> from zope.publisher.browser import TestRequest
  >>> from loops.i18n.browser import LanguageInfo
  >>> langInfo = LanguageInfo(topic01, TestRequest())
  >>> langInfo.availableLanguages
  []
  >>> langInfo.language is None
  True
  >>> langInfo.defaultLanguage is None
  True

In order to use content i18n we have to define the available languages
as an option on the loops root object.

  >>> loopsRoot.options = ['languages:en,de,it']
  >>> langInfo = LanguageInfo(topic01, TestRequest())
  >>> langInfo.availableLanguages
  ['en', 'de', 'it']
  >>> langInfo.defaultLanguage
  'en'
  >>> langInfo.language
  'en'

By setting an appropriate value in the URI we can select a certaing
language for processing of the current request.

  >>> input = {'loops.language': 'it'}
  >>> langInfo = LanguageInfo(topic01, TestRequest(form=input))
  >>> langInfo.availableLanguages
  ['en', 'de', 'it']
  >>> langInfo.defaultLanguage
  'en'
  >>> langInfo.language
  'it'

Let's now use a form to edit an i18n-sensible attribute. For this we have
to set up some components needed by the zope.formlib machinery.

  >>> from zope.publisher.interfaces.browser import IBrowserRequest
  >>> from zope.app.form.browser import TextWidget, ChoiceInputWidget, DropdownWidget
  >>> from zope.schema.interfaces import ITextLine, IText, IChoice
  >>> from zope.app.form.interfaces import IInputWidget
  >>> component.provideAdapter(TextWidget, (IText, IBrowserRequest),
  ...                          IInputWidget)
  >>> from loops.concept import ConceptTypeSourceList
  >>> from zope.schema.vocabulary import getVocabularyRegistry
  >>> getVocabularyRegistry().register('loops.conceptTypeSource', ConceptTypeSourceList)
  >>> component.provideAdapter(ChoiceInputWidget,
  ...          (IChoice, IBrowserRequest), IInputWidget)
  >>> component.provideAdapter(DropdownWidget,
  ...          (IChoice, ConceptTypeSourceList, IBrowserRequest), IInputWidget)

We also have to mark the attributes that should be stored in multiple
languages on the type object.

  >>> from loops.common import adapted
  >>> tTopic = adapted(topic)
  >>> tTopic.options = ['i18nattributes:title,description']

Now we are ready to enter a language-specific title.

  >>> from loops.browser.concept import ConceptEditForm, ConceptView
  >>> input = {'form.title': 'loops per Zope 3', 'loops.language': 'it',
  ...          'form.actions.apply': 'Change'}
  >>> form = ConceptEditForm(topic01, TestRequest(form=input))
  >>> form.update()

  >>> topic01.title
  {'en': u'loops for Zope 3', 'it': u'loops per Zope 3'}

If we access an i18n attribute via a view that is i18n-aware we get the
value corresponding to the language preferences that appear in the request.

  >>> input = {'loops.language': 'it'}
  >>> view = ConceptView(topic01, TestRequest(form=input))
  >>> view.title
  u'loops per Zope 3'

If there is no entry for the language given we get back the entry for
the default language.

  >>> input = {'loops.language': 'de'}
  >>> view = ConceptView(topic01, TestRequest(form=input))
  >>> view.title
  u'loops for Zope 3'

There are also fallbacks - mainly for being able to access the title
attribute in not i18n-aware contexts - that retrieve the value corresponding
to the default language at the time of the attribute creation.

  >>> topic01.title.getDefault()
  u'loops for Zope 3'
  >>> str(topic01.title)
  'loops for Zope 3'
  >>> topic01.title.lower()
  u'loops for zope 3'


Fin de partie
=============

  >>> placefulTearDown()

