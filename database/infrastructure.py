"""Constructs for Api Table"""
import logging

from aws_cdk import CfnOutput, aws_dynamodb
from constructs import Construct

logger = logging.getLogger(__name__)


class ApiDB(Construct):
    """Api Table CDK construct"""

    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        """Initialize persistence Table construct"""
        super().__init__(scope, id_, **kwargs)

        # create dynamo table
        self.api_table = aws_dynamodb.Table(
            self,
            "ApiTable",
            partition_key=aws_dynamodb.Attribute(
                name="id", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="sk", type=aws_dynamodb.AttributeType.STRING
            ),
        )
        logger.info(f"Created persistence table with id as pk, path as sk")

        # cloudformation resource output values
        table_arn_key = self.node.try_get_context("api_db_arn_output_key")
        table_name_key = self.node.try_get_context("api_db_name_output_key")
        CfnOutput(
            self,
            id="cfnApiTableARN",
            value=f"{self.api_table.table_arn}",
            export_name=f"{table_arn_key}",
        )
        logger.info(
            f"Added {table_arn_key}: {self.api_table.table_arn} to cfnOutPut"
        )
        CfnOutput(
            self,
            id="cfnApiTableName",
            value=f"{self.api_table.table_name}",
            export_name=f"{table_name_key}",
        )
        logger.info(
            f"Added {table_name_key}: {self.api_table.table_name} to cfnOutPut"
        )
