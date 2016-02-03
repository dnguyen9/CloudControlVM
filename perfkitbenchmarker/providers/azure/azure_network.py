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

"""Module containing classes related to Azure VM networking.

The Firewall class provides a way of opening VM ports. The Network class allows
VMs to communicate via internal ips and isolates PerfKitBenchmarker VMs from
others in
the same project. See http://msdn.microsoft.com/library/azure/jj156007.aspx
for more information about Azure Virtual Networks.
"""

import json
import uuid

from perfkitbenchmarker import flags
from perfkitbenchmarker import network
from perfkitbenchmarker import resource
from perfkitbenchmarker import vm_util
from perfkitbenchmarker import providers

FLAGS = flags.FLAGS
AZURE_PATH = 'azure'
MAX_NAME_LENGTH = 24
SSH_PORT = 22
# We need to prefix storage account names so that VMs won't create their own
# account upon creation.
# See https://github.com/MSOpenTech/azure-xplat-cli/pull/349
STORAGE_ACCOUNT_PREFIX = 'portalvhds'
RESOURCE_GROUP_PREFIX = 'portalrgrp'

class _AzureEndpoint(resource.BaseResource):
  """An object representing an endpoint to an Azure VM.
@@ -118,14 +118,61 @@ def DisallowAllPorts(self):
  No deletion is specified, as endpoints are deleted along with the VM.
  """
  def __init__(self, vm_name, port, protocol):
    super(_AzureEndpoint, self).__init__()
    self.vm_name = vm_name
    self.port = port
    self.protocol = protocol

  def _Create(self):
    create_cmd = [AZURE_PATH,
                  'vm',
                  'endpoint',
                  'create',
                  self.vm_name,
                  str(self.port),
                  '--protocol=' + self.protocol]
    vm_util.IssueCommand(create_cmd)

  def _Exists(self):
    """Returns whether or not an endpoint exists."""
    # Example output:
    # [
    #   {
    #     "localPort": 22,
    #     "name": "ssh",
    #     "port": 22,
    #     "protocol": "tcp",
    #     "virtualIPAddress": "104.43.224.13",
    #     "enableDirectServerReturn": false
    #   }
    # ]
    exists_cmd = [AZURE_PATH,
                  'vm',
                  'endpoint',
                  'list',
                  '--json',
                  self.vm_name]
    stdout, _, status = vm_util.IssueCommand(exists_cmd)
    if status or stdout == 'No VMs found':
      return False
    else:
      arr = json.loads(stdout)
      return any(ep['port'] == self.port and ep['protocol'] == self.protocol
                 for ep in arr)

  def _Delete(self):
    """Endpoint will be deleted with VM, so this is a noop."""
    pass


class AzureFirewall(network.BaseFirewall):
  """An object representing the Azure Firewall equivalent.

  On Azure, endpoints are used to open ports instead of firewalls.
  """

  CLOUD = providers.AZURE

  def AllowPort(self, vm, port):
    """Opens a port on the firewall.

    Args:
      vm: The BaseVirtualMachine object to open the port for.
      port: The local port to open.
    """
    if vm.is_static or port == SSH_PORT:
      return
    _AzureEndpoint(vm.name, port, 'tcp').Create()
    _AzureEndpoint(vm.name, port, 'udp').Create()

  def DisallowAllPorts(self):
    """Closes all ports on the firewall."""
    pass


class AzureResourceGroup(resource.BaseResource):
  """Object representing an Azure Resource group."""

  def __init__(self, name, storage_type, zone):
    super(AzureResourceGroup, self).__init__()
    self.name = name
    self.storage_type = storage_type
    self.zone = zone
    #Dien - create new variable to store group
#dd

  def _Create(self):
    """Creates the storage account."""
    create_cmd = [AZURE_PATH,
                  'group',
                  'create',
                  '--location=%s' % self.zone,
                  self.name]
    vm_util.IssueCommand(create_cmd)

  def _Delete(self):
    """Deletes the storage account."""
    delete_cmd = [AZURE_PATH,
                  'group',
                  'delete',
                  '--quiet',
                  self.name]
    vm_util.IssueCommand(delete_cmd)

  def _Exists(self):
    """Returns true if the storage account exists."""
    show_cmd = [AZURE_PATH,
                'group',
                'show',
                '--json',
                self.name]
    stdout, _, _ = vm_util.IssueCommand(show_cmd, suppress_warning=True)
    try:
      json.loads(stdout)
    except ValueError:
      return False
    return True


class AzureStorageAccount(resource.BaseResource):
  """Object representing an Azure Storage Account."""

  def __init__(self, name, storage_type, zone,resource_group):
    super(AzureStorageAccount, self).__init__()
    self.name = name
    self.storage_type = storage_type
    self.zone = zone
    self.resource_group = resource_group

    #Dien - create new variable to store group


  def _Create(self):
    """Creates the storage account."""
    create_cmd = [AZURE_PATH,
                  'storage',
                  'account',
                  'create',
                  '--location=%s' % self.zone,
                  '--type=%s' % self.storage_type,
                  '--resource-group=%s' % self.resource_group,
                  self.name]
    vm_util.IssueCommand(create_cmd)

  def _Delete(self):
    """Deletes the storage account."""
    delete_cmd = [AZURE_PATH,
                  'storage',
                  'account',
                  'delete',
                  '--resource-group=%s' % self.resource_group,
                  '--quiet',
                  self.name]
    vm_util.IssueCommand(delete_cmd)

  def _Exists(self):
    """Returns true if the storage account exists."""
    show_cmd = [AZURE_PATH,
                'storage',
                'account',
                'show',
                '--resource-group=%s' % self.resource_group,
                '--json',
                self.name]
    stdout, _, _ = vm_util.IssueCommand(show_cmd, suppress_warning=True)
    try:
      json.loads(stdout)
    except ValueError:
      return False
    return True


class AzureVirtualNetwork(resource.BaseResource):
  """Object representing an Azure Virtual Network."""

  def __init__(self, name, zone,resource_group):
    super(AzureVirtualNetwork, self).__init__()
    self.name = name
    self.zone = zone
    self.resource_group = resource_group

  def _Create(self):
    """Creates the virtual network."""
    create_cmd = [AZURE_PATH,
                  'network',
                  'vnet',
                  'create',
                  '--location', self.zone,
                  '--resource-group=%s' % self.resource_group,
                  self.name]
    vm_util.IssueCommand(create_cmd)

  def _Delete(self):
    """Deletes the virtual network."""
    delete_cmd = [AZURE_PATH,
                  'network',
                  'vnet',
                  'delete',
                  '--quiet',
                  '--resource-group=%s' % self.resource_group,
                  self.name]
    vm_util.IssueCommand(delete_cmd)

  def _Exists(self):
    """Returns true if the virtual network exists."""
    show_cmd = [AZURE_PATH,
                'network',
                'vnet',
                'show',
                '--resource-group=%s' % self.resource_group,
                '--json',
                self.name]
    stdout, _, _ = vm_util.IssueCommand(show_cmd, suppress_warning=True)
    vnet = json.loads(stdout)
    if vnet:
      return True
    return False


class AzureNetwork(network.BaseNetwork):
  """Object representing an Azure Network."""

  CLOUD = providers.AZURE

  def __init__(self, spec):
    super(AzureNetwork, self).__init__(spec)
    name = ('pkb%s%s' %
            (FLAGS.run_uri, str(uuid.uuid4())[-12:])).lower()[:MAX_NAME_LENGTH]
    storage_account_name = (STORAGE_ACCOUNT_PREFIX + name)[:MAX_NAME_LENGTH]
    resource_group_account = (RESOURCE_GROUP_PREFIX + name)[:MAX_NAME_LENGTH]

    self.resource_group_account = AzureResourceGroup(
        resource_group_account, FLAGS.azure_storage_type, self.zone)

    self.storage_account = AzureStorageAccount(
        storage_account_name, FLAGS.azure_storage_type, self.zone,resource_group_account)

    self.vnet = AzureVirtualNetwork(name, self.zone,resource_group_account)

  @vm_util.Retry()
  def Create(self):
    """Creates the actual network."""
    self.resource_group_account.Create()
    self.storage_account.Create()
    self.vnet.Create()

  def Delete(self):
    """Deletes the actual network."""
    self.vnet.Delete()
    self.storage_account.Delete()
    self.resource_group_account.Delete()
