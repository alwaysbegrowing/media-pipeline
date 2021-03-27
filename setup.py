import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="combine_lambda",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "combine_lambda"},
    packages=setuptools.find_packages(where="combine_lambda"),

    install_requires=[
        "aws-cdk.core==1.95.1",
        "aws-cdk.aws-lambda==1.95.1",
        "aws-cdk.aws-sqs==1.95.1",
        "aws-cdk.aws-mediaconvert==1.95.1",
        "aws-cdk.aws-lambda-event-sources==1.95.1",
        "boto3==1.17.39"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
