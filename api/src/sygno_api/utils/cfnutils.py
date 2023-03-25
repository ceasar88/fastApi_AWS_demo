"""Utilities for querying Cloudformation stacks"""
import boto3


def filter_cfn_outputs(outputs, export_name: str):
    """Filter CFn output values to one matching export_name

    Parameters
    ----------
    outputs: str
        list of Cfn Output Values
    export_name: str
        export name to match on

    Returns
    -------
    str
        matching CfnOutput value
    """
    return next(output for output in outputs if output["ExportName"] == export_name)


def get_stack_cfn_output_value(stack_name: str, export_name: str, cf_client=None):
    """Get Cloudformation output value from stack

    Parameters
    ----------
    stack_name: str
        Cloudformation stack name
    export_name: str
        CFn output value export name
    cf_client:
        boto3 client for cloudformation

    Returns
    -------
    dict
        Cfn Output value
    """

    if not cf_client:
        cf_client = boto3.client("cloudformation")
    response = cf_client.describe_stacks(StackName=stack_name)
    return filter_cfn_outputs(
        outputs=response["Stacks"][0]["Outputs"], export_name=export_name
    )
