import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="stack",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="PillarGG",

    package_dir={"": "stack"},
    packages=setuptools.find_packages(where="stack"),

    install_requires=[
        "aws_cdk.aws_lambda_python==1.95.1",
        "aws-cdk.core==1.95.1",
        "aws-cdk.aws-lambda==1.95.1",
        "aws-cdk.aws-s3==1.95.1",
        "aws-cdk.aws-s3-notifications==1.95.1",
        "aws-cdk.aws-mediaconvert==1.95.1",
        "aws-cdk.aws-lambda-event-sources==1.95.1",
        "aws-cdk.aws-lambda-python==1.95.1",
        "aws-cdk.aws-ecr==1.95.1",
        "aws-cdk.aws-stepfunctions==1.95.1",
        "aws-cdk.aws-stepfunctions-tasks==1.95.1",
        "aws-cdk.aws-secretsmanager==1.95.1"
        "boto3==1.17.39"
    ],

    python_requires=">=3.6",
)
