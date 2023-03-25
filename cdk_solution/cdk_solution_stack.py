"""Define stacks for deploying API service"""
from aws_cdk import Stack
from constructs import Construct

from api.infrastructure import SygnoAPI
from database.infrastructure import ApiDB


class CdkSolutionStack(Stack):
    """Stack for Api lambda function"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize Api Stack"""
        super().__init__(scope, construct_id, **kwargs)

        api_db = ApiDB(self, "ApiDB")

        SygnoAPI(self, "SygnoAPI", api_db=api_db)
