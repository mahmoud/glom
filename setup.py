import importlib.util
import os

from setuptools import setup

__author__ = 'Mahmoud Hashemi and Kurt Rose'
__contact__ = 'mahmoud@hatnote.com'
__url__ = 'https://github.com/mahmoud/glom'


def import_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CUR_PATH = os.path.abspath(os.path.dirname(__file__))
_version_mod_path = os.path.join(CUR_PATH, 'glom', '_version.py')
_version_mod = import_path('_version', _version_mod_path)
__version__ = _version_mod.__version__


open_kwarg = {}

with open('README.md', encoding='utf8') as read_me:
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
      install_requires=['boltons>=19.3.0', 'attrs', 'face>=20.1.1'],
      extras_require={
          'toml': ['tomli; python_version<"3.11"'],
          'yaml': ['PyYAML'],
      },
      entry_points={'console_scripts': ['glom = glom.cli:console_main']},
      include_package_data=True,
      zip_safe=False,
      platforms='any',
      license_files=['LICENSE'],
      classifiers=[
          'Topic :: Utilities',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'License :: OSI Approved :: BSD License',
      ]
     )

"""
A brief checklist for release:

* tox
* git commit (if applicable)
* Bump glom/_version.py off of -dev
* git commit -a -m "bump version for vx.y.z release"
* write CHANGELOG
* bump docs/conf.py version
* git commit
* rm -rf dist/*
* python setup.py sdist bdist_wheel
* twine upload dist/*
* git tag -a vx.y.z -m "brief summary"
* bump glom/_version.py onto n+1 dev
* git commit
* git push

NB: if dropping support for a python version, bump the pyupgrade argument in tox and run syntax-upgrade tox env.

"""
