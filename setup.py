#!/usr/bin/env python

from setuptools import setup, find_packages

install_require = [
    'flask',
    'nmeaserver>=0.1.9',
    'pycodestyle',
    'pytz',
]

tests_require = [
    'nose',
    'pytest',
]

setup(name='roboserver',
      version='1.0',
      description='Competition server used for RobotX, RoboBoat and more.',
      author='Bill Porter, Felix Pageau',
      author_email='william.porter@robotx.org, pageau@robonation.org',
      license='Apache License 2.0',
      url='https://github.com/robonation/roboserver',
      install_requires=install_require,
      tests_require=tests_require,
      test_suite='nose.collector',
      python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
      packages=find_packages(
          exclude=[
              "*.tests",
              "*.tests.*",
              "tests.*",
              "tests"]),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
      ],
      )
