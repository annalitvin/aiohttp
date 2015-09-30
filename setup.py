import codecs
import os
import re
import sys
from setuptools import setup, find_packages, Extension
from distutils.errors import (CCompilerError, DistutilsExecError,
                              DistutilsPlatformError)
from distutils.command.build_ext import build_ext
from setuptools.command.test import test as TestCommand


try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

ext = '.pyx' if USE_CYTHON else '.c'

extensions = [Extension('aiohttp._multidict', ['aiohttp/_multidict' + ext]),
              Extension('aiohttp._websocket', ['aiohttp/_websocket' + ext])]


if USE_CYTHON:
    extensions = cythonize(extensions)


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError,
                DistutilsPlatformError, ValueError):
            raise BuildFailed()


with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'aiohttp', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


install_requires = ['chardet']

if sys.version_info < (3, 4):
    install_requires += ['asyncio', 'enum34']


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


tests_require = install_requires + ['pytest', 'gunicorn']


args = dict(
    name='aiohttp',
    version=version,
    description=('http client/server for asyncio'),
    long_description='\n\n'.join((read('README.rst'), read('CHANGES.txt'))),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP'],
    author='Nikolay Kim',
    author_email='fafhrd91@gmail.com',
    url='https://github.com/KeepSafe/aiohttp/',
    license='Apache 2',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    include_package_data=True,
    ext_modules=extensions,
    cmdclass=dict(build_ext=ve_build_ext,
                  test=PyTest))

try:
    setup(**args)
except BuildFailed:
    print("************************************************************")
    print("Cannot compile C accelerator module, use pure python version")
    print("************************************************************")
    del args['ext_modules']
    del args['cmdclass']
    setup(**args)
