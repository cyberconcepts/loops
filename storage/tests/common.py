# loops.storage.test.common

"""Common definitions for testing the SQL-based storage implementation.
"""

import unittest
from zope import component, interface
from zope.app.testing.setup import placefulSetUp, placefulTearDown

from loops.expert.testsetup import TestSite
from loops.organize.setup import SetupManager
from loops.organize.tests import setupUtilitiesAndAdapters
from loops import util



class TestCase(unittest.TestCase):

    @classmethod
    def prepare(cls):
        cls.site = site = placefulSetUp(True)
        component.provideAdapter(SetupManager, name='organize')
        t = TestSite(site)
        cls.concepts, cls.resources, cls.views = t.setup()
        cls.loopsRoot = loopsRoot = site['loops']
        loopsId = util.getUidForObject(loopsRoot)
        setupData = setupUtilitiesAndAdapters(loopsRoot)

    @classmethod
    def cleanup(cls):
        placefulTearDown()


