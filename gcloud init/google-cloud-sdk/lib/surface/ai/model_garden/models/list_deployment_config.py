# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The command lists the deployment configurations of a given model supported by Model Garden."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_garden import client as client_mg
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import exceptions as core_exceptions


_DEFAULT_FORMAT = """
        table(
            dedicatedResources.machineSpec.machineType:label=MACHINE_TYPE,
            dedicatedResources.machineSpec.acceleratorType:label=ACCELERATOR_TYPE,
            dedicatedResources.machineSpec.acceleratorCount:label=ACCELERATOR_COUNT,
            containerSpec.imageUri:label=CONTAINER_IMAGE_URI
        )
    """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class ListDeployMentConfig(base.ListCommand):
  """List the machine specifications supported by and verified for a model in Model Garden.

  ## EXAMPLES

  To list the supported machine specifications for `google/gemma2@gemma-2-9b`,
  run:

    $ gcloud ai model-garden models list-deployment-config
    --model=google/gemma2@gemma-2-9b

  To list the supported machine specifications for a Hugging Face model
  `meta-llama/Meta-Llama-3-8B`, run:

    $ gcloud ai model-garden models list-deployment-config
    --model=meta-llama/Meta-Llama-3-8B
  """

  def _GetMultiDeploy(self, args, version):
    mg_client = client_mg.ModelGardenClient(version)
    # Convert to lower case because API only takes in lower case.
    publisher_name, model_name = args.model.lower().split('/')
    publisher_model = mg_client.GetPublisherModel(
        model_name=f'publishers/{publisher_name}/models/{model_name}',
        is_hugging_face_model='@' not in args.model,
    )

    try:
      multi_deploy = (
          publisher_model.supportedActions.multiDeployVertex.multiDeployVertex
      )
    except AttributeError:
      raise core_exceptions.Error(
          'Model does not support deployment, please enter a deploy-able model'
          ' instead. You can use the `gcloud ai model-garden models list`'
          ' command to find out which ones are currently supported by the'
          ' `deploy` command.'
      )
    return multi_deploy

  @staticmethod
  def Args(parser):
    # Remove the flags that are not supported by this command.
    base.LIMIT_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    base.Argument(
        '--model',
        help=(
            'The model to be deployed. If it is a Model Garden model, it should'
            ' be in the format of'
            ' `{publisher_name}/{model_name}@{model_version_name}, e.g.'
            ' `google/gemma2@gemma-2-2b`. If it is a Hugging Face model, it'
            ' should be in the convention of Hugging Face models, e.g.'
            ' `meta-llama/Meta-Llama-3-8B`.'
        ),
    ).AddToParser(parser)

  def Run(self, args):
    validation.ValidateModelGardenModelArgs(args)
    version = constants.BETA_VERSION

    with endpoint_util.AiplatformEndpointOverrides(
        version, region='us-central1'
    ):
      return self._GetMultiDeploy(args, version)
