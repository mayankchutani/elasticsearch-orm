#!/usr/bin/env python

from distutils.core import setup

setup(name='EsORM',
      version='1.0',
      description='Elasticsearch ORM',
      author='Mayank Chutani',
      author_email='mayankchutani.14@gmail.com',
      package_dir={'esorm': 'esorm'},
      packages=["esorm", "esorm.util", "esorm.config", "esorm.dao"]
     )