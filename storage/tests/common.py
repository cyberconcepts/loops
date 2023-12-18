# loops.storage.test.common

"""Common definitions for testing the SQL-based storage implementation.
"""

import config

import unittest
from zope import component, interface
from zope.app.testing.setup import placefulSetUp, placefulTearDown

from cco.storage.common import Storage, getEngine
from loops.expert.testsetup import TestSite
from loops.organize.personal.setup import SetupManager
from loops.organize.tests import setupObjectsForTesting
from loops import util

config.dbname = 'ccotest'
config.dbuser = 'ccotest'


class Glob(object):
    pass


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
        g.storage = Storage(getEngine('postgresql', 'ccotest', 'ccotest', 'cco'),
                            schema='testing')

    @classmethod
    def cleanup(cls):
        placefulTearDown()


