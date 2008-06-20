===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']
  >>> len(concepts), len(resources), len(views)
  (11, 3, 0)


Importing loops Objects
=======================

Reading object information from an external source
--------------------------------------------------

  >>> from loops.external.pyfunc import PyReader

  >>> input = ("concept('myquery', u'My Query', 'query', viewName='mystuff.html',"
  ...          "        options='option1\\noption2')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> elements
  [{'options': 'option1\noption2', 'type': 'query', 'name': 'myquery',
    'viewName': 'mystuff.html', 'title': u'My Query'}]

Creating the corresponding objects
----------------------------------

  >>> from loops.external.base import Loader

  >>> loader = Loader(loopsRoot)
  >>> loader.load(elements)
  >>> len(concepts), len(resources), len(views)
  (12, 3, 0)

  >>> from loops.common import adapted
  >>> adMyquery = adapted(concepts['myquery'])

  >>> adMyquery.viewName
  u'mystuff.html'
  >>> adMyquery.options
  [u'option1', u'option2']

Working with resources
----------------------

  >>> import os
  >>> from loops.external.tests import dataDirectory
  >>> loader.resourceDirectory = os.path.join(dataDirectory, 'import')

  >>> input = ("resource('doc04.txt', u'Document 4', 'textdocument')\n"
  ...          "resourceRelation('myquery', 'doc04.txt', 'standard')")
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> loader.load(elements)

  >>> sorted(resources)
  [u'd001.txt', u'd002.txt', u'd003.txt', u'doc04.txt']

Working with nodes
------------------

  >>> input = ("node('home', u'Home', '', u'menu', body=u'Welcome')\n"
  ...          "node('myquery', u'My Query', 'home', u'page', "
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

  >>> input = """concept('myquery', u'My Query', 'query', viewName='mystuff.html',
  ...                    options='option1\\noption2')[
  ...     annotations(creators=(u'john',))]"""
  >>> elements = reader.read(input)
  >>> elements[0].subElements
  [{'creators': (u'john',)}]

Loading the element with the sub-element stores the DC attributes.

  >>> loader.load(elements)
  >>> from zope.dublincore.interfaces import IZopeDublinCore
  >>> dc = IZopeDublinCore(concepts['myquery'])
  >>> dc.creators
  (u'john',)


Exporting loops Objects
=======================

Extracting elements
-------------------

  >>> from loops.external.base import Extractor
  >>> extractor = Extractor(loopsRoot, os.path.join(dataDirectory, 'export'))
  >>> elements = list(extractor.extract())
  >>> len(elements)
  20

Writing object information to the external storage
--------------------------------------------------

  >>> from loops.external.pyfunc import PyWriter
  >>> from cStringIO import StringIO

  >>> output = StringIO()
  >>> writer = PyWriter()
  >>> writer.write(elements, output)
  >>> print output.getvalue()
  type(u'customer', u'Customer', options=u'', typeInterface=u'', viewName=u'')...
  type(u'query', u'Query', options=u'', typeInterface='loops.query.IQueryConcept',
       viewName=u'')...
  concept(u'myquery', u'My Query', u'query', options=u'option1\noption2',
       viewName=u'mystuff.html')...
  child(u'projects', u'customer', u'standard')...
  resource(u'doc04.txt', u'Document 4', u'textdocument', contentType='text/restructured')
  resourceRelation(u'myquery', u'doc04.txt', u'standard')
  node('home', u'Home', '', u'menu', body=u'Welcome')
  node('myquery', u'My Query', 'home', u'page', target=u'concepts/myquery')...

Writing sub-elements
-------------------

Let's first set up a sequence with one element containing
two sub-elements.

  >>> input = """concept('myquery', u'My Query', 'query', viewName='mystuff.html')[
  ...     annotations(creators='john'),
  ...     annotations(modified='2007-08-12')]"""
  >>> elements = reader.read(input)
  >>> output = StringIO()
  >>> writer.write(elements, output)

Writing this sequence reproduces the import format.

  >>> print output.getvalue()
  concept('myquery', u'My Query', 'query', viewName='mystuff.html')[
      annotations(creators='john'),
      annotations(modified='2007-08-12')]...

DC annotations will be exported automatically after registering the
corresponding extractor adapter.

  >>> from loops.external.annotation import AnnotationsExtractor
  >>> component.provideAdapter(AnnotationsExtractor)

  >>> output = StringIO()
  >>> extractor = Extractor(loopsRoot, os.path.join(dataDirectory, 'export'))
  >>> PyWriter().write(extractor.extract(), output)

  >>> print output.getvalue()
  type(u'customer', u'Customer', options=u'', typeInterface=u'', viewName=u'')...
  concept(u'myquery', u'My Query', u'query', options=u'option1\noption2',
          viewName=u'mystuff.html')[
              annotations(creators=(u'john',))]...


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

