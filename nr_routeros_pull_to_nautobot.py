#!/usr/bin/python3
"""
This script gets device info and saves it to Nautobot.
"""

from ast import Num
import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import *
from config import *
from nr_routeros_general import *
from pynautobot import api
import logging

logging.basicConfig(filename='logs/nr_pull_to_nautobot.log', level=logging.DEBUG)

def translate_mt_interface_type(interface):
    '''
    Translates the Mikrotik interface type to the Nautobot interface type.
    '''
    int_type = None

    if interface['type'] == 'vlan':
        int_type = 'virtual'
    elif interface['type'] == 'bridge':
        int_type = 'virtual'
    elif 'default-name' in interface.keys():
        if 'ether' in interface['default-name']:
            int_type = '1000base-t'
        elif 'sfpplus' in interface['default-name']:
            int_type = '10gbase-x-sfpp'
        elif 'sfp' in interface['default-name']:
            int_type = '1000base-x-sfp'

    if not int_type:
        int_type = 'other'

    return int_type

def get_mikrotik_info(task: Task) -> Result:
    '''
    Gets routeros version, hardware, interfaces, and site from the device by calling other functions.
    '''
    # Get the routeros version
    routeros_version_result = task.run(
        task=get_ros_version,
    )

    # Get the hardware type
    hardware_result = task.run(
        task=get_hardware,
    )

    # Get the interfaces
    interfaces_result = task.run(
        task=get_interfaces,
    )

    # Get the site
    site_result = task.run(
        task=get_site,
    )

    # Get the role
    role_result = task.run(
        task=get_role,
    )

    # Get the serial number
    serial_result = task.run(
        task=get_serial,
    )

    # Get the IP addresses
    ip_addresses_result = task.run(
        task=get_ip_addresses,
    )

    # Create a string summary of the info gathered
    summary = f'''RouterOS version: {routeros_version_result.result}
    Hardware: {hardware_result.result}
    Interfaces: gathered
    Site: {site_result.result}
    Role: {role_result.result}
    Serial: {serial_result.result}
    IP Addresses: gathered'''

    return Result(
        host=task.host,
        result=summary,
    )

def create_nb_site(task: Task, nautobot: api) -> Result:
    '''
    Create a site in Nautobot based on the site name in the host's data.
    '''
    # Get the site name from the host's data
    site = task.host.data['site']

    # Check if the site already exists in Nautobot
    nb_site = nautobot.dcim.sites.get(name=site)

    # Create the site in Nautobot if it doesn't exist
    if not nb_site:
        nautobot.dcim.sites.create(
            name=site,
            status='active',
        )

    return Result(
        host=task.host,
        result=f'id: {nb_site.id}',
    )

def create_nb_device_type(task: Task, nautobot: api) -> Result:
    '''
    Create a device type in Nautobot based on the hardware type in the host's data.
    '''
    # Get the hardware type from the host's data
    hardware = task.host.data['hardware']

    # Check if the device type already exists in Nautobot
    nb_device_type = nautobot.dcim.device_types.get(model=hardware)

    # Create the device type in Nautobot if it doesn't exist
    if not nb_device_type:
        nautobot.dcim.device_types.create(
            model=hardware,
            manufacturer={'name':'MikroTik'},
        )
    
    return Result(
        host=task.host,
        result=f'id: {nb_device_type.id}',
    )

def create_nb_device(task: Task, nautobot: api) -> Result:
    '''
    Creates a device in Nautobot based on the site, hardware, and role in the host's data.
    '''
    # Get the site name from the host's data
    site = task.host.data['site']

    # Get the device type id from the host's data
    model = task.host.data['hardware']

    # Get the role from the host's data
    role = task.host.data['role']

    # Get the serial number from the host's data
    serial = task.host.data['serial']

    # Check if the device already exists in Nautobot
    device = nautobot.dcim.devices.get(name=task.host.name)

    # Create the device in Nautobot if it doesn't exist
    if not device:
        device = nautobot.dcim.devices.create(
            name=task.host.name,
            device_type={'model': model},
            site={'name': site},
            status='active',
            device_role={'name': role},
            serial=serial,
        )
    # Update the device if it does exist
    else:
        device.update({
            'device_type': {'model': model},
            'site': {'name': site},
            'status': 'active',
            'device_role': {'name': role},
            'serial': serial,
        })

    return Result(
        host=task.host,
        result=f'id: {device.id}',
    )

def create_nb_prefixes(task: Task, nautobot: api) -> Result:
    '''
    Create prefixes in Nautobot based on the IP addresses in the host's data.
    '''
    # Get the IP addresses from the host's data
    ip_addresses = task.host.data['ip_addresses']

    # Loop through the IP addresses
    for ip_address in ip_addresses:
        # Get the IP address
        address = ip_address['address']

        # Get the subnet length from the CIDR-notation address
        subnet_length = int(address.split('/')[1])

        # Find the subnet network address in CIDR notation based on the network property and subnet length
        subnet_network = ip_address['network'] + '/' + str(subnet_length)

        # Set status based on disabled status of the IP address
        if ip_address['disabled'] == 'false':
            status = 'active'
        else:
            status = 'deprecated'

        # Check if the prefix already exists in Nautobot
        nb_prefix_filter = nautobot.ipam.prefixes.filter(prefix=subnet_network)
        if len(nb_prefix_filter) > 0:
            nb_prefix = nb_prefix_filter[0]

            # Delete duplicate matches
            if len(nb_prefix_filter) > 1:
                for prefix in nb_prefix_filter[1:]:
                    prefix.delete()
        else:
            nb_prefix = None

        # Create the prefix in Nautobot if it doesn't exist
        if not nb_prefix:
            nautobot.ipam.prefixes.create(
                status=status,
                prefix=str(subnet_network),
            )
        # Update the prefix if it does exist
        else:
            nb_prefix.update({
                'status': status,
            })

    return Result(
        host=task.host,
        result=True,
    )

def create_nb_interfaces(task: Task, nautobot: api) -> Result:
    '''
    Create interfaces in Nautobot based on the interfaces in the host's data.
    '''
    # Get the interfaces from the host's data
    interfaces = task.host.data['interfaces']

    # Loop through the interfaces
    for interface in interfaces:
        # Get the interface name
        name = interface['name']

        # Get the interface description if a comment exists
        if 'comment' in interface.keys():
            description = interface['comment']
        else:
            description = ''

        # Find the nautobot interface type
        int_type = translate_mt_interface_type(interface)

        # Check if the interface already exists in Nautobot
        # Use default-name to filter the interface, otherwise use name (allows updating names instead of creating new)
        logging.debug(f'Checking for interface {name} on device {task.host.name} with mac {interface["mac-address"]}')
        if 'default-name' in interface.keys():
            nb_interface = nautobot.dcim.interfaces.get(
                cf_default_name=interface['default-name'],
                device=task.host.name,
                mac_address=interface['mac-address'],
            )
        else:
            nb_interface = nautobot.dcim.interfaces.get(
                name=name,
                device=task.host.name,
            )
        logging.debug(f'nb_interface: {nb_interface}')

        # Set blank default-name if no name exists
        if 'default-name' not in interface.keys():
            interface['default-name'] = ''

        # Create or update the interface in Nautobot
        if not nb_interface:
            try:
                logging.debug(f'Creating interface {name} on device {task.host.name}')
                nautobot.dcim.interfaces.create(
                    name=name,
                    status='active',
                    description=description,
                    mac_address=interface['mac-address'],
                    #mode='access',
                    #tags=[vlan],
                    type=int_type,
                    device={'name': task.host.name},
                )
            except Exception as e:
                pass
        # Update the interface if it does exist
        else:
            nb_interface.update({
                'status': 'active',
                'description': description,
                'mac_address': interface['mac-address'],
                #'mode': 'access',
                #'tags': [vlan],
                'type': int_type,
                'device': {'name': task.host.name},
                'custom_fields': {'default_name': interface['default-name']},
            })

    return Result(
        host=task.host,
        result=True,
    )

def create_nb_ip_addresses(task: Task, nautobot: api) -> Result:
    '''
    Create IP addresses in Nautobot based on the IP addresses in the host's data.
    '''
    # Get the IP addresses from the host's data
    ip_addresses = task.host.data['ip_addresses']

    # Loop through the IP addresses
    for ip_address in ip_addresses:
        # Get the IP address
        address = ip_address['address']

        # Get the subnet length from the CIDR-notation address
        subnet_length = int(address.split('/')[1])

        # Find the subnet network address in CIDR notation based on the network property and subnet length
        subnet_network = ip_address['network'] + '/' + str(subnet_length)

        # Set status based on disabled status of the IP address
        if ip_address['disabled'] == 'false':
            status = 'active'
        else:
            status = 'deprecated'

        # Set role based on subnet length
        if subnet_length == 32:
            role = 'loopback'
        else:
            role = None

        # If comment exists, use it as description.
        # Otherwise, set blank description.
        if 'comment' in ip_address.keys():
            description = ip_address['comment']
        else:
            description = ''

        # Check if the IP address already exists in Nautobot
        nb_ip_address_filter = nautobot.ipam.ip_addresses.filter(address=address)
        if len(nb_ip_address_filter) > 0:
            nb_ip_address = nb_ip_address_filter[0]

            # Delete duplicate matches
            if len(nb_ip_address_filter) > 1:
                for ip_address in nb_ip_address_filter[1:]:
                    ip_address.delete()
        else:
            nb_ip_address = None

        # Create the IP address in Nautobot if it doesn't exist
        if not nb_ip_address:
            nb_ip_address = nautobot.ipam.ip_addresses.create(
                address=address,
                status=status,
            )

        # Get the interface object
        nb_interface = nautobot.dcim.interfaces.get(
            name=ip_address['interface'],
            device=task.host.name,
        )
        
        # Update the IP address and assign it to interface
        nb_ip_address.update({
            'status': status,
            'description': description,
            'assigned_object_type': 'dcim.interface',
            'assigned_object_id': nb_interface.id,
            'role': role,
        })

def main():
    '''
    1. Gather info
    2. Create sites
    3. Create device_types
    4. Create devices
    5. Create interfaces
    6. Create prefixes
    7. Create IP addresses (assign to device)
    '''

    # initialize Nornir
    nr = InitNornir()

    # Save the first argument passed to the script as a variable called target if sys.argv[1] exists
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # If target is 'all', continue. Otherwise, filter the inventory using target as a hostname
    if target == 'all':
        pass
    else:
        nr = nr.filter(name=target).filter(F(groups__contains='routeros'))
        print(f'filtered inventory to {target}')

    # initialize pynautobot api
    nautobot = api(token=NB_TOKEN, url=NB_URL)

    # Gather info
    result = nr.run(
        task=get_mikrotik_info,
    )
    print_result(result)

    # Create a site in Nautobot
    result = nr.run(
        task=create_nb_site,
        nautobot=nautobot,
    )
    print_result(result)

    # Create a device type in Nautobot
    result = nr.run(
        task=create_nb_device_type,
        nautobot=nautobot,
    )
    print_result(result)

    # Create a device in Nautobot
    result = nr.run(
        task=create_nb_device,
        nautobot=nautobot,
    )
    print_result(result)

    # Create interfaces in Nautobot
    result = nr.run(
        task=create_nb_interfaces,
        nautobot=nautobot,
    )
    print_result(result)

    # Create prefixes in Nautobot
    result = nr.run(
        task=create_nb_prefixes,
        nautobot=nautobot,
    )
    print_result(result)

    # Create IP addresses in Nautobot
    result = nr.run(
        task=create_nb_ip_addresses,
        nautobot=nautobot,
    )
    print_result(result)

if __name__ == "__main__":
    main()