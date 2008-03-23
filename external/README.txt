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

  >>> input = "concept('myquery', u'My Query', 'query', viewName='mystuff.html')"
  >>> reader = PyReader()
  >>> elements = reader.read(input)
  >>> elements
  [{'type': 'query', 'name': 'myquery', 'viewName': 'mystuff.html', 'title': u'My Query'}]

Creating the corresponding objects
----------------------------------

  >>> from loops.external.base import Loader

  >>> loader = Loader(loopsRoot)
  >>> loader.load(elements)
  >>> len(concepts), len(resources), len(views)
  (12, 3, 0)

  >>> from loops.common import adapted
  >>> adapted(concepts['myquery']).viewName
  'mystuff.html'

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
  concept(u'myquery', u'My Query', u'query', options=u'', viewName='mystuff.html')...
  child(u'projects', u'customer', u'standard')...
  resource(u'doc04.txt', u'Document 4', u'textdocument', contentType='text/restructured')
  resourceRelation(u'myquery', u'doc04.txt', u'standard')
  node('home', u'Home', '', u'menu', body=u'Welcome')
  node('myquery', u'My Query', 'home', u'page', target=u'concepts/myquery')...


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
  ...     os.unlink(os.path.join(exportDir, fname))

