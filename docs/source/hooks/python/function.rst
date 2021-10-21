##############
PythonFunction
##############

This hook creates deployment packages for Python Lambda Functions, uploads them to S3, and returns data about the deployment package.

The return value can be retrieved using the :ref:`hook_data Lookup <hook_data lookup>` or by interacting with the :class:`~runway.context.CfnginContext` object passed to the |Blueprint|.

To use this hook, it must be able to find project metadata files.
This can include ``Pipefile`` & ``Pipfile.lock`` files (pipenv), a ``pyproject.toml`` & ``poetry.lock`` files (poetry), or a ``requirements.txt`` file (pip).
The project metadata files can exist either in the source code directory (value of ``source_code`` arg) or in the same directory as the CFNgin configuration file.
These files are required to defined the dependencies that will be included in the deployment package.

This hook will always use Docker to install/compile dependencies unless explicitly configured not to.
It is recommended to always use Docker to ensure a clean and consistent build.
It also ensures that binary files built during the install process are compatible with AWS Lambda.


.. contents:: Table of Contents
  :local:



****
Args
****

Arguments that can be passed to hook in the :attr:`~cfngin.hook.args` field.

Documentation for each field is automatically generated from class attributes in the source code.
When specifying the field, exclude the class name.

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.bucket_name
  :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.cache_dir
  :noindex:

  If not provided, the cache directory is ``.runway/awslambda/pip_cache`` within the current working directory.

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.docker
  :noindex:

  .. autoattribute:: awslambda.models.args.DockerOptions.disabled
    :noindex:

  .. autoattribute:: awslambda.models.args.DockerOptions.extra_files
    :noindex:

  .. autoattribute:: awslambda.models.args.DockerOptions.file
    :noindex:

  .. autoattribute:: awslambda.models.args.DockerOptions.image
    :noindex:

  .. autoattribute:: awslambda.models.args.DockerOptions.pull
    :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.extend_gitignore
  :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.object_prefix
  :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.runtime
  :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.source_code
  :noindex:

.. autoattribute:: awslambda.models.args.PythonFunctionHookArgs.use_cache
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

.. code-block:: docker
  :caption: Dockerfile

  FROM public.ecr.aws/sam/build-python3.9:latest

  RUN yum install libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel -y

.. code-block:: yaml
  :caption: cfngin.yml

  namespace: ${namespace}
  cfngin_bucket: ${cfngin_bucket}
  src_path: ./

  pre_deploy:
    - path: awslambda.PythonFunction
      data_key: awslambda.example-function
      args:
        bucket_name: ${bucket_name}
        docker:
          image: public.ecr.aws/sam/build-python3.9:latest
          pull: true
        extend_gitignore:
          - "*.lock"
          - '*.md'
          - '*.toml'
          - tests/
        extend_pip_args:
          - '--proxy'
          - '[user:passwd@]proxy.server:port'
        runtime: python3.9
        source_code: ./src/example-function
    - path: awslambda.PythonFunction
      data_key: awslambda.xmlsec
      args:
        bucket_name: ${bucket_name}
        docker:
          extra_files:
            - /usr/lib64/libxmlsec1-openssl.so
          file: ./Dockerfile
          pull: false
        extend_gitignore:
          - "*.lock"
          - '*.md'
          - '*.toml'
          - tests/
        runtime: python3.9
        source_code: ./src/xmlsec-function

  stacks:
    - name: example-stack
      class_path: blueprints.ExampleBlueprint
      parameters:
        XmlCodeSha256: ${awslambda.CodeSha256 awslambda.xmlsec}
        XmlRuntime: ${awslambda.Runtime awslambda.xmlsec}
        XmlS3Bucket: ${awslambda.S3Bucket awslambda.xmlsec}
        XmlS3Key: ${awslambda.S3Key awslambda.xmlsec}
    ...
