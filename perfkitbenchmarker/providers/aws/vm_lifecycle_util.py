# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for working with Amazon Web Services resources."""

import re
import string
import logging
import sys
import json


from perfkitbenchmarker import errors
from perfkitbenchmarker import flags
from perfkitbenchmarker import vm_util
from perfkitbenchmarker.providers.aws import util


AWS_PATH = 'aws'
AWS_PREFIX = [AWS_PATH, '--output', 'text']
AWS_REGIONS = {
               'us-east-1',
               'us-west-1',
               'us-west-2',
               'eu-west-1',
               'ap-northeast-1',
               'ap-southeast-1',
               'sa-east-1',
               'ap-southeast-2',}



def DoShutdownVM():

  for region in AWS_REGIONS:
    print region
    print _GetVMList(region)

def _GetVMList(region):
    """Returns the default image given the machine type and region.

    If no default is configured, this will return None.
    """

#aws  ec2 describe-instances --query 'Reservations[*].Instances[*][InstanceId,LaunchTime,PublicDnsName,Placement.AvailabilityZone,Tags[0].Value]' --filters "Name=instance-state-name,Values=running" --output table --region
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'ec2',
        'describe-instances',
        '--query', 'Reservations[*].Instances[*].{InstanceId:InstanceId}',
        '--filters',
        "Name=instance-state-name,Values=running"]
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None

#    print json.dumps(vm)
    vm =stdout.split()
    return vm





def CheckAWSVersion():
  """Warns the user if the Azure CLI isn't the expected version."""
  version_cmd = [AWS_PATH, 'version']
  try:
    stdout, _, _ = vm_util.IssueCommand(version_cmd,1)
  except OSError:
    # IssueCommand will raise an OSError if the CLI is not installed on the
    # system. Since we don't want to warn users if they are doing nothing
    # related to Azure, just do nothing if this is the case.
    return
  logging.warning(stdout.strip())


def IsRegion(zone_or_region):
  """Returns whether "zone_or_region" is a region."""
  if not re.match(r'[a-z]{2}-[a-z]+-[0-9][a-z]?$', zone_or_region):
    raise ValueError(
        '%s is not a valid AWS zone or region name' % zone_or_region)
  return zone_or_region[-1] in string.digits


def GetRegionFromZone(zone_or_region):
  """Returns the region a zone is in (or "zone_or_region" if it's a region)."""
  if IsRegion(zone_or_region):
    return zone_or_region
  return zone_or_region[:-1]


def AddTags(resource_id, region, **kwargs):
  """Adds tags to an AWS resource created by PerfKitBenchmarker.

  Args:
    resource_id: An extant AWS resource to operate on.
    region: The AWS region 'resource_id' was created in.
    **kwargs: dict. Key-value pairs to set on the instance.
  """
  if not kwargs:
    return

  tag_cmd = AWS_PREFIX + [
      'ec2',
      'create-tags',
      '--region=%s' % region,
      '--resources', resource_id,
      '--tags']
  for key, value in kwargs.iteritems():
    tag_cmd.append('Key={0},Value={1}'.format(key, value))
  IssueRetryableCommand(tag_cmd)


def AddDefaultTags(resource_id, region):
  """Adds tags to an AWS resource created by PerfKitBenchmarker.

  By default, resources are tagged with "owner" and "perfkitbenchmarker-run"
  key-value
  pairs.

  Args:
    resource_id: An extant AWS resource to operate on.
    region: The AWS region 'resource_id' was created in.
  """
  tags = {'owner': FLAGS.owner, 'perfkitbenchmarker-run': FLAGS.run_uri}
  AddTags(resource_id, region, **tags)


@vm_util.Retry()
def IssueRetryableCommand(cmd, env=None):
  """Tries running the provided command until it succeeds or times out.

  On Windows, the AWS CLI doesn't correctly set the return code when it
  has an error (at least on version 1.7.28). By retrying the command if
  we get output on stderr, we can work around this issue.

  Args:
    cmd: A list of strings such as is given to the subprocess.Popen()
        constructor.
    env: An alternate environment to pass to the Popen command.

  Returns:
    A tuple of stdout and stderr from running the provided command.
  """
  stdout, stderr, retcode = vm_util.IssueCommand(cmd,force_info_log=0, env=env)
  if retcode:
    raise errors.VmUtil.CalledProcessException(
        'Command returned a non-zero exit code.\n')
  if stderr:
    raise errors.VmUtil.CalledProcessException(
        'The command had output on stderr:\n%s' % stderr)
  return stdout, stderr
