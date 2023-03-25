#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_solution.cdk_solution_stack import CdkSolutionStack


app = cdk.App()
CdkSolutionStack(app, "cdk-solution")

app.synth()
