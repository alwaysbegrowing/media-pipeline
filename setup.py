import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="render_lambda",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="PillarGG",

    package_dir={"": "render_lambda"},
    packages=setuptools.find_packages(where="render_lambda"),

    install_requires=[
        "aws-cdk.core==1.95.1",
        "aws-cdk.aws-lambda==1.95.1",
        "aws-cdk.aws-sqs==1.95.1",
        "aws-cdk.aws-mediaconvert==1.95.1",
        "aws-cdk.aws-lambda-event-sources==1.95.1",
        "boto3==1.17.39"
    ],

    python_requires=">=3.6",
)
