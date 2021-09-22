# runway-hook-awslambda

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/runway-hook-awslambda/badge/?version=latest)](https://runway-hook-awslambda.readthedocs.io/en/latest/?badge=latest)

> **[DISCLAIMER]** This is a _temporary_ project being used to develop & test a feature that will be added to [Runway](runway) in a future release.
> Expect frequency, drastic, and breaking changes during development so use at your own risk.
>
> As this project reaches certain _milestones_ in development, there will be a versioned release.
> Feel free to test the released versions and provide feedback (in the form of issues) to help shape the final release.

This hooks is being developed as a successor to [aws_lambda.upload_lambda_functions](https://docs.onica.com/projects/runway/en/stable/cfngin/hooks.html#aws-lambda-upload-lambda-functions).
The new hooks is **NOT backward compatible** - arguments, behaviors, and features will vary.
However, the goal is to produce an end result that is more stable and user friendly than what is currently implemented while also being much more extensible.

When this is eventually released as part of [Runway](runway), the current hook will be retained until the next major release.
There will be a deprecation warning added to the current hook stating that it will be removed in the next major release.

## Prerequisites

- Python ^3.8 (will be lowered to 3.7 for the final release)
- pip

### Optional Prerequisites

- [poetry](https://python-poetry.org/) installed globally (if testing with a poetry project)

[runway]: https://github.com/onicagroup/runway
