##############
PythonFunction
##############

This hook creates deployment packages for Python Lambda Functions, uploads them to S3, and returns data about the deployment package.

The return value can be retrieved using the :ref:`hook_data Lookup <hook_data lookup>` or by interacting with the :class:`~runway.context.CfnginContext` object passed to the |Blueprint|.

To use this hook, it must be able to find project metadata files.
This can include ``Pipefile`` & ``Pipfile.lock`` files (pipenv), a ``pyproject.toml`` & ``poetry.lock`` files (poetry), or a ``requirements.txt`` file (pip).
The project metadata files can exist either in the source code directory (value of ``source_code`` arg) or in the same directory as the CFNgin configuration file.
These files are required to defined the dependencies that will be included in the deployment package.


.. contents:: Table of Contents
  :local:



****
Args
****

Arguments that can be passed to hook as the :attr:`~cfngin.hook.args` field.

.. autoclass:: awslambda.models.args.PythonFunctionHookArgs
  :exclude-members: Config
  :member-order: alphabetical
  :no-inherited-members:
  :no-show-inheritance:
  :no-special-members:
  :noindex:


************
Return Value
************

.. autoclass:: awslambda.models.responses.AwsLambdaHookDeployResponse
  :exclude-members: Config
  :member-order: alphabetical
  :no-inherited-members:
  :no-show-inheritance:
  :no-special-members:
  :noindex:


*******
Example
*******

.. code-block:: yaml

  pre_deploy:
    - path: awslambda.PythonFunction
      data_key: awslambda.test-function
      args:
        bucket_name: ${bucket_name}
        extend_gitignore:
          - '*.md'
          - tests/
        extend_pip_args:
          - '--proxy'
          - '[user:passwd@]proxy.server:port'
        runtime: python3.9
        source_code: ./src
