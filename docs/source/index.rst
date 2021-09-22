.. _Runway: https://github.com/onicagroup/runway
.. _submodule: https://git-scm.com/book/en/v2/Git-Tools-Submodules

#####################
runway-hook-awslambda
#####################

.. important::
  This is a temporary project being used to develop & test a feature that will be added to Runway_ in a future release.
  Expect frequency, drastic, and breaking changes during development so use at your own risk.

  As this project reaches certain milestones in development, there will be a versioned release.
  Feel free to test the released versions and provide feedback (in the form of issues) to help shape the final release.


*******
Testing
*******

This project can be tested while it is still under development.

#. Install this project from GitHub.
   The following example shows how to do this if using poetry.
   After manually adding the dependency, ``poetry lock && poetry install`` will need to be run to upload the lockfile and install dependencies.

   .. code-block:: toml
    :caption: pyproject.toml

    [tool.poetry.dependencies]
    # this can be used to get the latest updates (not recommended)
    awslambda = { git = "https://github.com/ITProKyle/runway-hook-awslambda.git", branch = "master" }
    # this can be used to test from a specific commit if a feature has not yet been included in a tagged version
    awslambda = { git = "https://github.com/ITProKyle/runway-hook-awslambda.git", rev = "abc123" }
    # this can be used to test a tagged version (recommended)
    awslambda = { git = "https://github.com/ITProKyle/runway-hook-awslambda.git", tag = "v0.1.0" }

#. Use the hooks & lookups as documented.


.. toctree::
  :caption: Hooks
  :glob:
  :hidden:
  :maxdepth: 2

  hooks/**


.. toctree::
  :caption: Developers Guide
  :hidden:
  :maxdepth: 2

  apidocs/index
