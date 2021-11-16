.. _AWS::Lambda::LayerVersion.License: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-layerversion.html#cfn-lambda-layerversion-license

#################
awslambda.License
#################

.. automodule:: awslambda_lookup._lookup
  :exclude-members: AwsLambdaLookup
  :noindex:

A string or ``None`` is returned by this lookup.
The returned value can be passed directly to `AWS::Lambda::LayerVersion.License`_.


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
        License: ${awslambda.License example-layer-01}
        ...
    - name: example-stack-02
      template_path: ./templates/bar-stack.yml
      variables:
        License: ${awslambda.License example-layer-02}
        ...
