# loops.storage.tests.common

"""Common definitions for testing the SQL-based storage implementation.
"""

import config
config.dbname = 'ccotest'
config.dbuser = 'ccotest'
config.dbpassword = 'cco'

import unittest
from zope import component, interface
from zope.app.testing.setup import placefulSetUp, placefulTearDown

from loops.expert.testsetup import TestSite
from loops.organize.personal.setup import SetupManager
from loops.organize.tests import setupObjectsForTesting
from loops.storage.compat.common import StorageFactory
from loops import util

util.storageFactory = StorageFactory(config)


class Glob(object):

    storage = util.storageFactory(schema='testing')
    

class TestCase(unittest.TestCase):

    @classmethod
    def prepare(cls):
        cls.site = site = placefulSetUp(True)
        component.provideAdapter(SetupManager, name='organize.personal')
        t = TestSite(site)
        cls.g = g = Glob()
        g.concepts, g.resources, g.views = t.setup()
        cls.loopsRoot = loopsRoot = site['loops']
        loopsId = util.getUidForObject(loopsRoot)
        setupData = setupObjectsForTesting(site, g.concepts)
        g.johnC = setupData.johnC

    @classmethod
    def cleanup(cls):
        placefulTearDown()


