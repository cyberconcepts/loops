"""
Set up a loops site for testing.

$Id$
"""

import os
from zope import component
from zope.app.catalog.interfaces import ICatalog
from zope.app.catalog.field import FieldIndex

from loops import util
from loops.concept import Concept
from loops.constraint.base import StaticConstraint
from loops.constraint.setup import SetupManager
from loops.setup import addAndConfigureObject
from loops.tests.setup import TestSite as BaseTestSite


class TestSite(BaseTestSite):

    def __init__(self, site):
        self.site = site

    def setup(self):
        component.provideAdapter(SetupManager, name='constraint')
        concepts, resources, views = self.baseSetup()

        component.provideAdapter(StaticConstraint)

        return concepts, resources, views

