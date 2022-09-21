from aws_cdk import CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_cloudtrail as cloudtrail
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_glue_alpha as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct


class BaseStack(Stack):  # type: ignore
    def __init__(self, scope: Construct, construct_id: str, **kwargs: str) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "aws-sdk-pandas-vpc",
            cidr="11.19.224.0/19",
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )
        Tags.of(self.vpc).add("Name", "aws-sdk-pandas")
        self.key = kms.Key(
            self,
            id="aws-sdk-pandas-key",
            description="AWS SDK for pandas Test Key.",
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="Enable IAM User Permissions",
                        effect=iam.Effect.ALLOW,
                        actions=["kms:*"],
                        principals=[iam.AccountRootPrincipal()],
                        resources=["*"],
                    )
                ]
            ),
        )
        kms.Alias(
            self,
            "aws-sdk-pandas-key-alias",
            alias_name="alias/aws-sdk-pandas-key",
            target_key=self.key,
        )
        self.bucket = s3.Bucket(
            self,
            id="aws-sdk-pandas",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="CleaningUp",
                    enabled=True,
                    expiration=Duration.days(1),
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                ),
            ],
            versioned=True,
        )
        glue_db = glue.Database(
            self,
            id="aws_sdk_pandas_glue_database",
            database_name="aws_sdk_pandas",
            location_uri=f"s3://{self.bucket.bucket_name}",
        )
        log_group = logs.LogGroup(
            self,
            id="aws_sdk_pandas_log_group",
            retention=logs.RetentionDays.ONE_MONTH,
        )
        log_stream = logs.LogStream(
            self,
            id="aws_sdk_pandas_log_stream",
            log_group=log_group,
        )

        self.trail = cloudtrail.Trail(
            self,
            id="Bucket Trail",
        )
        self.trail.add_s3_event_selector(
            [
                cloudtrail.S3EventSelector(bucket=self.bucket),
            ]
        )

        CfnOutput(self, "Region", value=self.region)
        CfnOutput(
            self,
            "VPC",
            value=self.vpc.vpc_id,
            export_name="aws-sdk-pandas-base-VPC",
        )
        CfnOutput(
            self,
            "PublicSubnet1",
            value=self.vpc.public_subnets[0].subnet_id,
            export_name="aws-sdk-pandas-base-PublicSubnet1",
        )
        CfnOutput(
            self,
            "PublicSubnet2",
            value=self.vpc.public_subnets[1].subnet_id,
            export_name="aws-sdk-pandas-base-PublicSubnet2",
        )
        CfnOutput(
            self,
            "PublicSubnet3",
            value=self.vpc.public_subnets[2].subnet_id,
            export_name="aws-sdk-pandas-base-PublicSubnet3",
        )
        CfnOutput(
            self,
            "PrivateSubnet",
            value=self.vpc.private_subnets[0].subnet_id,
            export_name="aws-sdk-pandas-base-PrivateSubnet",
        )
        CfnOutput(
            self,
            "KmsKeyArn",
            value=self.key.key_arn,
            export_name="aws-sdk-pandas-base-KmsKeyArn",
        )
        CfnOutput(
            self,
            "BucketName",
            value=self.bucket.bucket_name,
            export_name="aws-sdk-pandas-base-BucketName",
        )
        CfnOutput(self, "GlueDatabaseName", value=glue_db.database_name)
        CfnOutput(self, "LogGroupName", value=log_group.log_group_name)
        CfnOutput(self, "LogStream", value=log_stream.log_stream_name)

    @property
    def get_bucket(self) -> s3.Bucket:
        return self.bucket

    @property
    def get_vpc(self) -> ec2.Vpc:
        return self.vpc

    @property
    def get_key(self) -> kms.Key:
        return self.key
