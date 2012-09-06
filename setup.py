#!/usr/bin/env python

import os

from setuptools import setup, find_packages

VERSION = '0.1.10'

if __name__ == '__main__':
    setup(
        name = 'django-pushserver',
        version = VERSION,
        description = "Push server for Django based on Leo Ponomarev's Basic HTTP Push Relay Protocol.",
        long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
        author = 'Mitar',
        author_email = 'mitar.django@tnode.com',
        url = 'https://github.com/mitar/django-pushserver',
        license = 'AGPLv3',
        packages = find_packages(),
        package_data = {},
        classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Framework :: Django',
        ],
        include_package_data = True,
        zip_safe = False,
        dependency_links = [
            'https://github.com/mitar/py-hbpush/tarball/0.1.3-mitar#egg=py_hbpush-0.1.3',
            'http://github.com/clement/brukva/tarball/bff451511a3cc09cd52bebcf6372a59d36567827#egg=brukva-0.0.1',
        ],
        install_requires = [
            'Django>=1.2',
            'py_hbpush==0.1.3',
        ],
    )
