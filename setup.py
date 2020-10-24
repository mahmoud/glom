import imp
import os
import sys

from setuptools import setup

__author__ = 'Mahmoud Hashemi and Kurt Rose'
__contact__ = 'mahmoud@hatnote.com'
__url__ = 'https://github.com/mahmoud/glom'
__license__ = 'BSD'

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
_version_mod_path = os.path.join(CUR_PATH, 'glom', '_version.py')
_version_mod = imp.load_source('_version', _version_mod_path)
__version__ = _version_mod.__version__


open_kwarg = {}
if sys.version_info[0] == 3:
    open_kwarg['encoding'] = 'utf-8'

with open('README.md', **open_kwarg) as read_me:
    long_description = read_me.read()

setup(name='glom',
      version=__version__,
      description="A declarative object transformer and formatter, for conglomerating nested data.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author=__author__,
      author_email=__contact__,
      url=__url__,
      project_urls={
          'Documentation': 'https://glom.readthedocs.io/en/latest/',
      },
      packages=['glom', 'glom.test'],
      install_requires=['boltons>=19.3.0', 'attrs', 'face>=20.1.0'],
      extras_require={
          'yaml': ['PyYAML'],
      },
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
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy', ]
     )

"""
A brief checklist for release:

* tox
* git commit (if applicable)
* Bump glom/_version.py off of -dev
* git commit -a -m "bump version for vx.y.z release"
* rm -rf dist/*
* python setup.py sdist bdist_wheel
* twine upload dist/*
* bump docs/conf.py version
* git commit
* git tag -a vx.y.z -m "brief summary"
* write CHANGELOG
* git commit
* bump glom/_version.py onto n+1 dev
* git commit
* git push

"""
