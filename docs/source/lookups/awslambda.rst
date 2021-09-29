#########
awslambda
#########

.. automodule:: awslambda_lookup._lookup
  :exclude-members: AwsLambdaLookup
  :noindex:

An :class:`~awslambda.models.responses.AwsLambdaHookDeployResponse` object is returned by this lookup.
It is recommended to only use this lookup when passing the value into a :class:`~runway.cfngin.blueprints.base.Blueprint` or hook as further processing will be required.


.. rubric:: Example
.. code-block:: yaml

  namespace: example
  cfngin_bucket: ''
  sys_path: ./

  lookups:
    awslambda: awslambda_lookup.AwsLambdaLookup

  pre_deploy:
    - path: awslambda.PythonFunction
      data_key: example-function-01
      args:
        ...
    - path: awslambda.PythonFunction
      data_key: example-function-02
      args:
        ...

  stacks:
    - name: example-stack-01
      class_path: blueprints.FooStack
      variables:
        code_metadata: ${awslambda example-function-01}
        ...
    - name: example-stack-02
      class_path: blueprints.BarStack
      variables:
        code_metadata: ${awslambda example-function-02}
        ...
