.. _AWS::Lambda::Function.Runtime: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html#cfn-lambda-function-runtime

#################
awslambda.Runtime
#################

.. automodule:: awslambda_lookup._lookup
  :exclude-members: AwsLambdaLookup
  :noindex:

A string is returned by this lookup.
The returned value can be passed directly to `AWS::Lambda::Function.Runtime`_.
While not necessary, using this hook to fill in ``Runtime`` ensures compatibility with the deployment package and removes the need for duplicating configuration values.


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
        Runtime: ${awslambda.Runtime example-function-01}
        ...
    - name: example-stack-02
      template_path: ./templates/bar-stack.yml
      variables:
        Runtime: ${awslambda.Runtime example-function-02}
        ...
