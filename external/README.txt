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


Exporting loops Objects
=======================

Extracting elements
-------------------

  >>> from loops.external.base import Extractor

  >>> extractor = Extractor(loopsRoot)
  >>> elements = list(extractor.extract())
  >>> len(elements)
  13

Writing object information to the external storage
--------------------------------------------------

  >>> from loops.external.pyfunc import PyWriter
  >>> from cStringIO import StringIO

  >>> output = StringIO()
  >>> writer = PyWriter()
  >>> writer.write(elements, output)
  >>> print output.getvalue()
  type(u'customer', u'Customer', options=u'', viewName=u'')...
  type(u'query', u'Query', options=u'', typeInterface='loops.query.IQueryConcept',
       viewName=u'')...
  concept(u'myquery', u'My Query', u'query', viewName='mystuff.html')...
  child(u'projects', u'customer', u'standard')...


The Export/Import View
======================

  >>> from loops.external.browser import ExportImport
  >>> from zope.publisher.browser import TestRequest

  >>> input = {'field.data': output}
  >>> view = ExportImport(loopsRoot, TestRequest(input))
  >>> view.upload()
  False
