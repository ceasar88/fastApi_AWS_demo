"""DynamoDB utility methods"""

import logging

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", "us-west-1")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_table(table_name: str) -> dynamodb.Table:
    """Get API table
    Parameters
    ----------
    table_name: str
        dynamoDB table name we are fetching
    Returns
    -------
    table
        dynamoDB table with matching table name
    """
    try:
        table = dynamodb.Table(table_name)
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
    else:
        return table
