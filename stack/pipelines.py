from aws_cdk import core as cdk
from aws_cdk import pipelines
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_codepipeline as codepipeline

class RenderLambdaPipeline(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)



        source_artifact = codepipeline.Artifact()
        cloudAssemblyArtifact = codepipeline.Artifact()

        pipeline = pipelines.CdkPipeline(self, 'RenderLambdaPipeline',
                                        # pipeline name and assembly
                                        pipeline_name='RenderLambdaPipeline',
                                        cloud_assembly_artifact=cloudAssemblyArtifact,

                                        # where the code comes from
                                        source_action=codepipeline_actions.GitHubSourceAction(
                                            action_name='GitHubRenderLambda',
                                            output=source_artifact,
                                            oauth_token=cdk.SecretValue.secrets_manager('github-token'),
                                            owner='pillargg',
                                            repo='render-lambda'
                                        ),

                                        synth_action= # https://aws.amazon.com/blogs/developer/cdk-pipelines-continuous-delivery-for-aws-cdk-applications/

        )
                                        