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
from tabulate import tabulate

from perfkitbenchmarker import errors
from perfkitbenchmarker import flags
from perfkitbenchmarker import vm_util
from perfkitbenchmarker.providers.aws import util


AWS_PATH = 'aws'
AWS_PREFIX = [AWS_PATH, '--output', 'json']
AWS_REGIONS = {
               'us-east-1',
               'us-west-1',
               'us-west-2',
               'eu-west-1',
               'ap-northeast-1',
               'ap-northeast-2',
               'ap-southeast-1',
               'sa-east-1',
               'ap-southeast-2',}

AWS_EXCLUDE_SHUTDOWN  = {
               'i-35c644bc',
               'i-78b09de0',}
AWS_STOP_ALL_VMS = 'no'

def DoShutdownVM():

  vm_tables = []
  storage_cost = {'gp2':0,'io1':0,'standard':0, 'Iops':0, 'Snapshot':0}
  rds_tables = []
  for region in AWS_REGIONS:
    print "Traversing in region: ", region
    vm_list =  _GetVMList(region)
    vm_json = json.loads(vm_list)
    storage_list = _ListVolumes(region)
    storage_json = json.loads(storage_list)
    rds_list = _ListRDSInstances(region)
    rds_json = json.loads(rds_list)

    if rds_json <> None:
        for instance in rds_json['DBInstances']:
            rds_info = [region, instance['Engine'],instance['DBInstanceClass'],instance['AllocatedStorage'], instance['DBInstanceStatus']]
            rds_tables.append(rds_info)

    for volume in storage_json:
      type = volume['VolumeType']
      size =  volume['Size']
      storage_cost[type] = size + storage_cost[type]
      if type == 'io1':
          storage_cost['Iops'] = storage_cost['Iops'] +  volume['Iops']

    if vm_json  <> None:
        for vm in vm_json['Reservations']:
             tag ="N/A"
             try:
                 tag = vm['Instances'][0]['Tags'][0]['Value']
                 print tag
             except Exception:
                 pass

             vm_info = [region,
                        vm['Instances'][0]['InstanceId'],
                        tag,
                        vm['Instances'][0]['State']['Name'],
                        vm['Instances'][0]['InstanceType'],
                        vm['Instances'][0]['LaunchTime'],
                        vm['Instances'][0]['KeyName'],
                        vm['Instances'][0]['StateTransitionReason']]
             vm_tables.append(vm_info)
             if vm_info[2] == 'running' and (not vm_info[1] in AWS_EXCLUDE_SHUTDOWN) and AWS_STOP_ALL_VMS == 'yes':
                 print "Shutting down running instance:", vm_info[1]
                 _StopInstance(vm_info[1],region)

  print tabulate(vm_tables,["Region","InstanceId","Name", "Status","Size","Launch Date", "Key","StateTransitionReason"])
  print tabulate(rds_tables,["Region","DBInstance","DB_Size","Size_GB","Status"])
  print 'Daily Storage cost:'
  print  tabulate([['GP2 SSD',storage_cost['gp2'],round(storage_cost['gp2'] * .10 / 30,3)],
                 ['Provioned IOPS',storage_cost['io1'],round((storage_cost['io1'] * .125 + storage_cost['Iops'] * .065) / 30,3)],
                 ['Standard',storage_cost['standard'],round(storage_cost['standard'] * .05 /30,3)]],
                 ["Storage Type","Size_GB","Daily Cost $"])

def _GetVMList(region):
    """Returns the default image given the machine type and region.

    If no default is configured, this will return None.
    """

#aws  ec2 describe-instances --query 'Reservations[*].Instances[*][InstanceId,LaunchTime,PublicDnsName,Placement.AvailabilityZone,Tags[0].Value]' --filters "Name=instance-state-name,Values=running" --output table --region
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'ec2',
        'describe-instances']
#        '--query', 'Reservations[*].Instances[*].{InstanceId:InstanceId}',
#        '--filters',
#        "Name=instance-state-name,Values=running"]
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None

    return stdout

def _StopInstance(instance_ids, region):
    #aws ec2 stop-instances  --instance-ids i-77ade2ad --region us-west-2
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'ec2',
        'stop-instances',
        '--instance-ids=%s' % instance_ids]
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None

    return stdout
def _ListVolumes(region):
    #PS C:\Users\dnguyen> aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone,Size:Size}'
    #aws ec2 stop-instances  --instance-ids i-77ade2ad --region us-west-2
    #aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'ec2',
        'describe-volumes',
        '--query', 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone,Iops:Iops,Size:Size}',]
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None

    return stdout

def _ListSnapshots(region):
    #PS C:\Users\dnguyen> aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone,Size:Size}'
    #aws ec2 stop-instances  --instance-ids i-77ade2ad --region us-west-2
    #aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'ec2',
        'describe-snapshots']
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None
    return stdout

def _ListRDSInstances(region):
    #PS C:\Users\dnguyen> aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone,Size:Size}'
    #aws ec2 stop-instances  --instance-ids i-77ade2ad --region us-west-2
    #aws ec2 describe-volumes --query 'Volumes[*].{ID:VolumeId,VolumeType:VolumeType,AZ:AvailabilityZone
    describe_cmd = AWS_PREFIX + [
        '--region=%s' % region,
        'rds',
        'describe-db-instances']
    stdout, _ = IssueRetryableCommand(describe_cmd)

    if not stdout:
      return None
    return stdout

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
