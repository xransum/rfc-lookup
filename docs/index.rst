RFC Lookup
==============================

.. toctree::
   :hidden:
   :maxdepth: 1

   reference
   contributing
   code_of_conduct
   license

This project is a simple command-line interface that allows for easily looking
up and searching for RFCs from the command line. It uses the resources provided
by `IETF <https://www.ietf.org/>`_ and the `RFC Editor <https://www.rfc-editor.org/>`_
to provide the most up-to-date information on RFCs.


Installation
------------

To install the RFC Lookup project,
run this command in your terminal:

.. code-block:: console

   $ pip install rfc-lookup


Usage
-----

RFC Lookup's usage looks like:

.. code-block:: console

   $ rfc [OPTIONS] COMMAND [ARGS]...

.. option:: --version

   Display the version and exit.

.. option:: --help

   Display a short usage message and exit.



Commands
--------

Get
^^^^

The ``get`` command retrieves the RFC with the given number.

.. code-block:: console

   $ rfc get [RFC_NUMBER] [OPTIONS]

.. option:: --url

   Display the URL of the RFC.


Search
^^^^^^

The ``search`` command searches for RFCs with the given query.

.. code-block:: console

   $ rfc search [QUERY] [OPTIONS]
