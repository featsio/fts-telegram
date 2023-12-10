========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/fts-telegram/badge/?style=flat
    :target: https://fts-telegram.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/andreoliwa/fts-telegram/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/andreoliwa/fts-telegram/actions

.. |codecov| image:: https://codecov.io/gh/andreoliwa/fts-telegram/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://app.codecov.io/github/andreoliwa/fts-telegram

.. |version| image:: https://img.shields.io/pypi/v/fts-telegram.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/fts-telegram

.. |wheel| image:: https://img.shields.io/pypi/wheel/fts-telegram.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/fts-telegram

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/fts-telegram.svg
    :alt: Supported versions
    :target: https://pypi.org/project/fts-telegram

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/fts-telegram.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/fts-telegram

.. |commits-since| image:: https://img.shields.io/github/commits-since/andreoliwa/fts-telegram/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/andreoliwa/fts-telegram/compare/v0.0.0...master



.. end-badges

Telegram crawler for Feats

* Free software: MIT license

Installation
============

::

    pip install fts-telegram

You can also install the in-development version with::

    pip install https://github.com/andreoliwa/fts-telegram/archive/master.zip


Documentation
=============


https://fts-telegram.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
