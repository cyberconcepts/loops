
import unittest, doctest
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass


class Test(unittest.TestCase):
    "Basic tests for the i18n sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
