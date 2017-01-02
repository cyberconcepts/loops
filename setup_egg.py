from setuptools import setup, find_packages
import sys, os

version = '2.2.1'

setup(name='loops',
      version=version,
      description="loops",
      long_description="""\
linked objects for organizational process services""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='cyberconcepts.org team',
      author_email='team@cyberconcepts.org',
      url='https://www.cyberconcepts.org',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'zope.app.securitypolicy',
          'zope.app.session',
          'cybertools',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
