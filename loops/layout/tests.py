# loops.layout.tests

import unittest, doctest

from zope import component
from loops.layout.base import NodeLayoutInstance, SubnodesLayoutInstance
from loops.layout.base import TargetLayoutInstance

def setup():
    component.provideAdapter(NodeLayoutInstance)
    component.provideAdapter(SubnodesLayoutInstance, name='subnodes')
    component.provideAdapter(TargetLayoutInstance, name='target')


class Test(unittest.TestCase):
    "Basic tests for the layout sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
        unittest.TestLoader().loadTestsFromTestCase(Test),
        doctest.DocFileSuite('README.txt', optionflags=flags),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
