"""*glom gets results.*

To be more precise, glom helps pull together objects from other
objects in a declarative, dynamic, and downright simple way.

Built with services, APIs, and general serialization in mind, glom
helps filter objects as well as perform deep fetches which would be
tedious to perform in a procedural manner.

Where "schema" and other libraries focus on validation and parsing
less-structured data into Python objects, glom goes the other
direction, producing more-readily serializable data from valid
higher-level objects.

"""

from setuptools import setup


__author__ = 'Mahmoud Hashemi'
__version__ = '18.1.1'
__contact__ = 'mahmoud@hatnote.com'
__url__ = 'https://github.com/mahmoud/glom'
__license__ = 'BSD'


setup(name='glom',
      version=__version__,
      description="A declarative object transformer and formatter, for conglomerating nested data.",
      long_description=__doc__,
      author=__author__,
      author_email=__contact__,
      url=__url__,
      packages=['glom', 'glom.test'],
      install_requires=['boltons', 'attrs', 'face'],
      entry_points={'console_scripts': ['glom = glom.cli:console_main']},
      include_package_data=True,
      zip_safe=False,
      license=__license__,
      platforms='any',
      classifiers=[
          'Topic :: Utilities',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy', ]
      )

"""
A brief checklist for release:

* tox
* git commit (if applicable)
* Bump setup.py version off of -dev
* git commit -a -m "bump version for x.y.z release"
* python setup.py sdist bdist_wheel upload
* bump docs/conf.py version
* git commit
* git tag -a vx.y.z -m "brief summary"
* write CHANGELOG
* git commit
* bump setup.py version onto n+1 dev
* git commit
* git push

"""
