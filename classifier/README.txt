===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Automatic classification of resources.

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

  >>> from loops.classifier.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> len(concepts), len(resources)
  (20, 0)

Let's now add an external collection that reads in a set of resources
from external files so we have something to work with.

  >>> from loops.concept import Concept
  >>> from loops.setup import addObject
  >>> from loops.common import adapted
  >>> from loops.classifier.testsetup import dataDir

  >>> tExternalCollection = concepts['extcollection']
  >>> coll01 = addObject(concepts, Concept, 'coll01',
  ...                    title=u'Collection One', conceptType=tExternalCollection)
  >>> aColl01 = adapted(coll01)
  >>> aColl01.baseAddress = dataDir
  >>> aColl01.address = ''

  >>> aColl01.update()
  >>> len(resources)
  7
  >>> rnames = list(sorted(resources.keys()))
  >>> rnames[0]
  u'cust_im_contract_webbg_20071015.txt'


Filename-based Classification
=============================

Let's first look at the external address (i.e. the file name) of the
resource we want to classify.

  >>> r1 = resources[rnames[0]]
  >>> adapted(r1)
  <loops.resource.ExternalFileAdapter object ...>
  >>> adapted(r1).externalAddress
  'cust_im_contract_webbg_20071015.txt'

OK, that's what we need. So we get the preconfigured classifier
(see testsetup.py) and let it classify the resource.

  >>> classifier = adapted(concepts['fileclassifier'])

Before just processing the resource we'll have a look at the details
and follow the classifier step by step.

  >>> from loops.classifier.base import InformationSet
  >>> from loops.classifier.interfaces import IExtractor, IAnalyzer
  >>> infoSet = InformationSet()
  >>> for name in classifier.extractors.split():
  ...     print 'extractor:', name
  ...     extractor = component.getAdapter(adapted(r1), IExtractor, name=name)
  ...     infoSet.update(extractor.extractInformationSet())
  extractor: filename

  >>> infoSet
  {'filename': 'cust_im_contract_webbg_20071015'}

Let's now use the sample analyzer - an example that interprets very carefully
the underscore-separated parts of the filename.

  >>> analyzer = component.getAdapter(classifier, name=classifier.analyzer)
  >>> statements = analyzer.extractStatements(infoSet)
  >>> statements
  []

So there seems to be something missing - we have to create concepts
that may be identified as being candidates for classification.

  >>> tInstitution = addObject(concepts, Concept, 'institution',
  ...                     title=u'Institution', conceptType=concepts['type'])
  >>> cust_im = addObject(concepts, Concept, 'im_editors',
  ...                     title=u'im Editors', conceptType=tInstitution)
  >>> cust_mc = addObject(concepts, Concept, 'mc_consulting',
  ...                     title=u'MC Management Consulting', conceptType=tInstitution)

  >>> tDoctype = addObject(concepts, Concept, 'doctype',
  ...                     title=u'Document Type', conceptType=concepts['type'])
  >>> dt_note = addObject(concepts, Concept, 'dt_note',
  ...                     title=u'Note', conceptType=tDoctype)
  >>> dt_contract = addObject(concepts, Concept, 'dt_contract',
  ...                     title=u'Contract', conceptType=tDoctype)

  >>> tPerson = concepts['person']
  >>> webbg = addObject(concepts, Concept, 'webbg',
  ...                     title=u'Gerald Webb', conceptType=tPerson)
  >>> smitha = addObject(concepts, Concept, 'smitha',
  ...                     title=u'Angelina Smith', conceptType=tPerson)
  >>> watersj = addObject(concepts, Concept, 'watersj',
  ...                     title=u'Jerry Waters', conceptType=tPerson)
  >>> millerj = addObject(concepts, Concept, 'millerj',
  ...                     title=u'Jeannie Miller', conceptType=tPerson)

  >>> t.indexAll(concepts, resources)

  >>> from zope.app.catalog.interfaces import ICatalog
  >>> cat = component.getUtility(ICatalog)

  >>> statements = analyzer.extractStatements(infoSet)
  >>> len(statements)
  3

So we are now ready to have the whole stuff run in one call.

  >>> classifier.process(r1)
  >>> list(sorted([c.title for c in r1.getConcepts()]))
  [u'Collection One', u'Contract', u'External File', u'Gerald Webb', u'im Editors']

  >>> for name in rnames[1:]:
  ...     classifier.process(resources[name])
  >>> len(webbg.getResources())
  4
  >>> len(webbg.getResources((concepts['ownedby'],)))
  3

We can repeat the process without getting additional assignments.

  >>> for name in rnames[1:]:
  ...     classifier.process(resources[name])
  >>> len(webbg.getResources())
  4


Fin de partie
=============

  >>> placefulTearDown()
