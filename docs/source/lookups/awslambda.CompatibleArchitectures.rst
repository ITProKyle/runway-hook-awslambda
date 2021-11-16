.. _AWS::Lambda::LayerVersion.CompatibleArchitectures: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-layerversion.html#cfn-lambda-layerversion-compatiblearchitectures

#################################
awslambda.CompatibleArchitectures
#################################

.. automodule:: awslambda_lookup._lookup
  :exclude-members: AwsLambdaLookup
  :noindex:

A list of strings or ``None`` is returned by this lookup.
The returned value can be passed directly to `AWS::Lambda::LayerVersion.CompatibleArchitectures`_.


.. rubric:: Arguments

This lookup only supports the ``transform`` argument which can be used to turn the list of strings into a comma delimited list.


.. rubric:: Example
.. code-block:: yaml

  namespace: example
  cfngin_bucket: ''
  sys_path: ./

  lookups:
    awslambda: awslambda_lookup.AwsLambdaLookup

  pre_deploy:
    - path: awslambda.PythonLayer
      data_key: example-layer-01
      args:
        ...
    - path: awslambda.PythonLayer
      data_key: example-layer-02
      args:
        ...

  stacks:
    - name: example-stack-01
      class_path: blueprints.FooStack
      variables:
        CompatibleArchitectures: ${awslambda.CompatibleArchitectures example-layer-01}
        ...
    - name: example-stack-02
      template_path: ./templates/bar-stack.yml
      variables:
        CompatibleArchitectures: ${awslambda.CompatibleArchitectures example-layer-02::transform=str}
        ...
