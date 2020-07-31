.. _version_guarantees:

Version Guarantees
=====================

The library follows a `semantic versioning principle <https://semver.org/>`_ which means that the major version is updated every time there is an incompatible API change. However due to the lack of guarantees on the Discord side when it comes to breaking changes along with the fairly dynamic nature of Python it can be hard to discern what can be considered a breaking change and what isn't.

The first thing to keep in mind is that breaking changes only apply to **publicly documented functions and classes**. If it's not listed in the documentation here then it is not part of the public API and is thus bound to change. This includes attributes that start with an underscore or functions without an underscore that are not documented.

.. note::

    The examples below are non-exhaustive.

Examples of Breaking Changes
------------------------------

- Changing the default parameter value to something else.
- Renaming a function without an alias to an old function.
- Adding or removing parameters to an event.

Examples of Non-Breaking Changes
----------------------------------

- Adding or removing private underscored attributes.
- Adding an element into the ``__slots__`` of a data class.
- Changing the behaviour of a function to fix a bug.
- Changes in the documentation.
- Modifying the internal HTTP handling.
- Upgrading the dependencies to a new version, major or otherwise.

