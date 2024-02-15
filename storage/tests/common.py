# loops.storage.tests.common

"""Common definitions for testing the SQL-based storage implementation.
"""

import config
import scopes.storage.common
from scopes.storage.common import getEngine, sessionFactory

config.dbname = 'ccotest'
config.dbuser = 'ccotest'
config.dbpassword = 'cco'
engine = getEngine(config.dbengine, config.dbname, 
                   config.dbuser, config.dbpassword, 
                   host=config.dbhost, port=config.dbport)
scopes.storage.common.engine = engine
scopes.storage.common.Session = sessionFactory(engine)

import unittest
from zope import component, interface
from zope.app.testing.setup import placefulSetUp, placefulTearDown

from loops.expert.testsetup import TestSite
from loops.organize.personal.setup import SetupManager
from loops.organize.tests import setupObjectsForTesting
from loops.storage.compat.common import Storage
from loops import util


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
        g.storage = Storage(schema='testing')

    @classmethod
    def cleanup(cls):
        placefulTearDown()


