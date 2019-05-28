#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='RoboServer',
	  version='1.0',
	  description='Competition server used for RobotX, RoboBoat and more.',
	  author='Bill Porter, Felix Pageau',
	  author_email='bill.porter@robotx.org, pageau@robonation.org',
	  license='Apache License 2.0',
	  url='https://github.com/robonation/roboserver',
	  install_requires=['pycodestyle'],
	  python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
	  packages=find_packages(),
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
