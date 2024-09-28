===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  >>> from zope import component
  >>> from zope.traversing.api import getName

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.expert.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']
  >>> len(concepts), len(resources), len(views)
  (35, 3, 1)


Importing loops Objects
=======================

Reading object information from an external source
--------------------------------------------------

  >>> from loops.external.pyfunc import PyReader

  >>> input = ("concept('myquery', 'My Query', 'query', viewName='mystuff.html',"
  ...          "        options='option1\\noption2')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> elements
  [{'name': 'myquery', ...}]

[{'options': 'option1\noption2', 'type': 'query', 'name': 'myquery',
  'viewName': 'mystuff.html', 'title': 'My Query'}]

Creating the corresponding objects
----------------------------------

  >>> from loops.external.base import Loader

  >>> loader = Loader(loopsRoot)
  >>> loader.load(elements)
  >>> len(concepts), len(resources), len(views)
  (36, 3, 1)

  >>> from loops.common import adapted
  >>> adMyquery = adapted(concepts['myquery'])

  >>> adMyquery.viewName
  'mystuff.html'
  >>> adMyquery.options
  ['option1', 'option2']

Importing types
---------------

  >>> input = ("type('mytype', 'My Type',"
  ...          "        typeInterface='loops.expert.concept.IQueryConcept')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> loader = Loader(loopsRoot)
  >>> loader.load(elements)

  >>> adapted(concepts['mytype']).typeInterface
  <InterfaceClass loops.expert.concept.IQueryConcept>

Working with resources
----------------------

  >>> input = ("resource('doc04.txt', 'Document 4', 'textdocument')\n"
  ...          "resourceRelation('myquery', 'doc04.txt', 'standard')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)

  >>> import os
  >>> from loops.external.tests import dataDirectory
  >>> loader = Loader(loopsRoot, os.path.join(dataDirectory, 'import'))
  >>> loader.load(elements)

  >>> sorted(resources)
  ['d001.txt', 'd002.txt', 'd003.txt', 'doc04.txt']

Working with nodes
------------------

  >>> input = ("node('home', 'Home', '', 'menu', body='Welcome')\n"
  ...          "node('myquery', 'My Query', 'home', 'page', "
  ...          "     target='concepts/myquery')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> loader.load(elements)

Sub-elements
------------

Complex attributes or other informations related to an object may be
represented by sub-elements. The standard example for this kind of data
are the Dublin Core (DC) attributes.

By importing the annotation module the corresponding element class will be
registered.

  >>> from loops.external import annotation

  >>> input = """concept('myquery', 'My Query', 'query', viewName='mystuff.html',
  ...                    options='option1\\noption2')[
  ...     annotations(creators=('john',))]"""
  >>> elements = reader.read(input)
  >>> elements[0].subElements
  [{'creators': ('john',)}]

Loading the element with the sub-element stores the DC attributes.

  >>> loader.load(elements)
  >>> from zope.dublincore.interfaces import IZopeDublinCore
  >>> dc = IZopeDublinCore(concepts['myquery'])
  >>> dc.creators
  ('john',)


Exporting loops Objects
=======================

Extracting elements
-------------------

  >>> from loops.external.base import Extractor
  >>> extractor = Extractor(loopsRoot, os.path.join(dataDirectory, 'export'))
  >>> elements = list(extractor.extract())
  >>> len(elements)
  69

Writing object information to the external storage
--------------------------------------------------

  >>> from loops.external.pyfunc import PyWriter
  >>> from io import StringIO

  >>> output = StringIO()
  >>> writer = PyWriter()
  >>> writer.write(elements, output)
  >>> print(output.getvalue())
  type('task', ...)...

type('country', 'Country', viewName='', typeInterface=''..., options=''...)...
  type('query', 'Query', viewName='', typeInterface='loops.expert.concept.IQueryConcept'..., options=''...)...
  concept('myquery', 'My Query', 'query', options='option1\noption2',
       viewName='mystuff.html'...)...
  child('projects', 'customer', 'standard')...
  resource('doc04.txt', 'Document 4', 'textdocument', contentType='')...
  resourceRelation('myquery', 'doc04.txt', 'standard')
  node('home', 'Home', '', 'menu')
  node('myquery', 'My Query', 'home', 'page', target='concepts/myquery')...

Writing sub-elements
-------------------

Let's first set up a sequence with one element containing
two sub-elements.

  >>> input = """concept('myquery', 'My Query', 'query', viewName='mystuff.html')[
  ...     annotations(creators='john'),
  ...     annotations(modified='2007-08-12')]"""
  >>> elements = reader.read(input)
  >>> output = StringIO()
  >>> writer.write(elements, output)

Writing this sequence reproduces the import format.

  >>> print(output.getvalue())
  concept('myquery', 'My Query', 'query', viewName='mystuff.html')[
      annotations(creators='john'),
      annotations(modified='2007-08-12')]...

DC annotations will be exported automatically after registering the
corresponding extractor adapter.

  >>> from loops.external.annotation import AnnotationsExtractor
  >>> component.provideAdapter(AnnotationsExtractor)

  >>> output = StringIO()
  >>> extractor = Extractor(loopsRoot, os.path.join(dataDirectory, 'export'))
  >>> PyWriter().write(extractor.extract(), output)

  >>> print(output.getvalue())
  type('task', ...)...

type('country', 'Country', viewName='', typeInterface=''..., options=''...)...
  concept('myquery', 'My Query', 'query', options='option1\noption2',
          viewName='mystuff.html')[
              annotations(creators=('john',))]...

Extracting selected parts of the concept map
--------------------------------------------

  >>> extractor = Extractor(loopsRoot, os.path.join(dataDirectory, 'export'))
  >>> elements = list(extractor.extractForParents([concepts['customer']],
  ...                       includeSubconcepts=True, includeResources=True))
  >>> len(elements)
  10

  >>> output = StringIO()
  >>> writer.write(elements, output)
  >>> print(output.getvalue())
  type('customer', 'Customer', ...)
  concept('cust1', 'Customer 1', 'customer')
  concept('cust2', 'Customer 2', 'customer')
  concept('cust3', 'Customer 3', 'customer')
  resource('d001.txt', 'Doc 001', 'textdocument', contentType='')
  resource('d003.txt', 'Doc 003', 'textdocument', contentType='')
  resource('d002.txt', 'Doc 002', 'textdocument', contentType='')
  resourceRelation('cust1', 'd001.txt', 'standard')
  resourceRelation('cust1', 'd003.txt', 'standard')
  resourceRelation('cust3', 'd002.txt', 'standard')


The Export/Import View
======================

  >>> from loops.external.browser import ExportImport
  >>> from zope.publisher.browser import TestRequest

  >>> input = {'field.data': output, 'resourceDirectory': dataDirectory}
  >>> view = ExportImport(loopsRoot, TestRequest(input))
  >>> view.upload()
  False


Fin de Partie
=============

  >>> placefulTearDown()

  >>> exportDir = os.path.join(dataDirectory, 'export')
  >>> for fname in os.listdir(exportDir):
  ...     path = os.path.join(exportDir, fname)
  ...     if not os.path.isdir(path):
  ...         os.unlink(path)

