from aws_cdk import core as cdk
from aws_cdk import pipelines
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_codepipeline as codepipeline

from stack.pipeline_stages import PreprodStage, ProdStage
# used this as reference
# https://aws.amazon.com/blogs/developer/cdk-pipelines-continuous-delivery-for-aws-cdk-applications/


class RenderLambdaPipeline(cdk.Stack):

    def __init__(
            self,
            scope: cdk.Construct,
            construct_id: str,
            **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloudAssemblyArtifact = codepipeline.Artifact()

        pipeline = pipelines.CdkPipeline(self, 'RenderLambdaPipeline',
                                         # pipeline name and assembly
                                         pipeline_name='PreProdRenderLambdaPipeline',
                                         cloud_assembly_artifact=cloudAssemblyArtifact,

                                         # where the code comes from
                                         source_action=codepipeline_actions.GitHubSourceAction(
                                             action_name='GitHubRenderLambda',
                                             output=source_artifact,
                                             oauth_token=cdk.SecretValue.secrets_manager(
                                                 'github-token', json_field='chand1012'),
                                             owner='pillargg',
                                             repo='render-lambda',
                                             branch='develop'
                                         ),

                                         # synthesises the code
                                         # if this were a typescript project
                                         # it would also compile
                                         synth_action=pipelines.SimpleSynthAction(
                                             install_commands=[
                                                 'npm i -g aws-cdk',
                                                 'pip install -r ./requirements.txt'
                                             ],
                                             synth_command="cdk synth",
                                             source_artifact=source_artifact,
                                             cloud_assembly_artifact=cloudAssemblyArtifact,
                                             environment={'privileged': True}
                                             # build_commands=['npm run build']
                                         )
                                         )

        pipeline.add_application_stage(PreprodStage(self, 'PreProd'))


class ProdRenderLambdaPipeline(cdk.Stack):
    def __init__(
            self,
            scope: cdk.Construct,
            construct_id: str,
            **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloudAssemblyArtifact = codepipeline.Artifact()

        pipeline = pipelines.CdkPipeline(self, 'ProdRenderLambdaPipeline',
                                         # pipeline name and assembly
                                         pipeline_name='ProdRenderLambdaPipeline',
                                         cloud_assembly_artifact=cloudAssemblyArtifact,

                                         # where the code comes from
                                         source_action=codepipeline_actions.GitHubSourceAction(
                                             action_name='GitHubRenderLambda',
                                             output=source_artifact,
                                             oauth_token=cdk.SecretValue.secrets_manager(
                                                 'github-token', json_field='chand1012'),
                                             owner='pillargg',
                                             repo='render-lambda',
                                             branch='master'
                                         ),

                                         # synthesises the code
                                         # if this were a typescript project
                                         # it would also compile
                                         synth_action=pipelines.SimpleSynthAction(
                                             install_commands=[
                                                 'npm i -g aws-cdk',
                                                 'pip install -r ./requirements.txt'
                                             ],
                                             synth_command="cdk synth",
                                             source_artifact=source_artifact,
                                             cloud_assembly_artifact=cloudAssemblyArtifact,
                                             environment={'privileged': True}
                                             # build_commands=['npm run build']
                                         )
                                         )

        pipeline.add_application_stage(ProdStage(self, 'Prod'))
