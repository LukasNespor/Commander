from setuptools import setup
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    read_md = lambda f: open(f, 'r').read()
from os import path

import keepercommander

LICENSE = open("LICENSE").read()

# strip links from the descripton on the PyPI
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
    'colorama',
    'pycrypto',
    'requests',
    'tabulate',
    'click',
]

setup(name='keepercommander',
      version=keepercommander.__version__,
      description='Keeper Commander for Python 3',
      long_description=read_md('README.md'),
      author='Craig Lurey',
      author_email='craig@keepersecurity.com',
      url='https://github.com/Keeper-Security/Commander',
      license='MIT',
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.4",
                   "Topic :: Security"],
      keywords='security password',

      packages=['keepercommander'],

      entry_points={
          "console_scripts": [
              "keeper=keepercommander:main",
          ],
      },
      install_requires=install_requires
      )