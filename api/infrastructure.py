"""Constructs for the API service"""
import os
import typing

from aws_cdk import Aws, CfnOutput, aws_ecr
from aws_cdk import aws_iam as iam  # Duration
from aws_cdk import aws_lambda
from constructs import Construct

from database.infrastructure import ApiDB


class SygnoAPI(Construct):
    """SygnoAPI CDK construct"""

    def __init__(self, scope: Construct, id_: str, api_db: ApiDB):
        """Initialize API construct"""
        super().__init__(scope, id_)

        image_name = "cdk_solution"
        #
        # If use_pre_existing_image is True
        # then use an image that already exists in ECR.
        # Otherwise, build a new image
        #
        use_pre_existing_image = False

        # ECR

        ecr_repository = aws_ecr.Repository.from_repository_attributes(
            self,
            id="ECR",
            repository_arn=f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}",
            repository_name=image_name,
        )

        # ensure we can push/pull repository from gitlab runners on EC2
        ecr_repository.grant_pull_push(iam.ServicePrincipal("ec2.amazonaws.com"))

        if use_pre_existing_image:
            # Container was built previously, or elsewhere.
            # Use the pre-existing container

            # ecr_image is expecting a `Code` type, so casting
            # `EcrImageCode` to `Code` resolves mypy error
            ecr_image = typing.cast(
                "aws_lambda.Code", aws_lambda.EcrImageCode(repository=ecr_repository)
            )

        else:
            # Create new Container Image.
            ecr_image = aws_lambda.EcrImageCode.from_asset_image(
                directory=os.path.join(os.getcwd(), "api/src")
            )

        # set database permissions
        api_table = api_db.api_table
        api_table_arn = api_table.table_arn
        dynamodb_access_policy = iam.Policy(
            self,
            "DynamoTableAcsPlcy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:Scan",
                        "dynamodb:DescribeTable",
                        "dynamodb:ConditionCheckItem",
                    ],
                    resources=[
                        api_table_arn,
                        f"{api_table_arn}/index/*",
                    ],
                ),
            ],
        )

        lambda_log_access_policy = iam.Policy(
            self,
            "LogAcsPlcy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "cloudwatch:PutMetricData",
                    ],
                    resources=["*"],
                ),
            ],
        )

        role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        role.attach_inline_policy(dynamodb_access_policy)
        role.attach_inline_policy(lambda_log_access_policy)

        # Lambda Function
        application = "api-solution"
        deploy_env = "cdk"
        component = "dev"
        lambda_fn = aws_lambda.Function(
            self,
            id="ApiFunction",
            description="Api Service Lambda Container Function",
            code=ecr_image,
            handler=aws_lambda.Handler.FROM_IMAGE,  # Handler and Runtime must be *FROM_IMAGE*
            runtime=aws_lambda.Runtime.FROM_IMAGE,  # when provisioning Lambda from Container.
            environment={
                "APPLICATION": application,
                "DEPLOY_ENV": deploy_env,
                "COMPONENT": component,
                "Api_TABLE_NAME": api_table.table_name,
            },
            role=role
            # timeout=Duration.seconds(10),
        )

        lambda_fn.add_permission(
            "APIGateway",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
        )

        lambda_key = self.node.try_get_context("lambda_arn_output_key")
        CfnOutput(
            self,
            id="cfnApiFunctionARN",
            value=f"{lambda_fn.function_arn}",
            export_name=f"{lambda_key}",
        )
