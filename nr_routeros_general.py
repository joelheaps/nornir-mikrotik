#!/bin/bash
from nornir_routeros.plugins.tasks import *
from nornir.core.task import Task, Result
import subprocess
from config import *
from nornir.core.filter import F

def ssh_command(task, command) -> Result:
    '''
    Runs a command on the device using the systems's SSH command and returns the output of the command as result.
    Connect using subprocess.run and SSH.
    '''
    username = task.host.username
    password = task.host.password

    # Generate the full command to run on the device
    full_command = f'sshpass -p {password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {username}@{task.host.hostname} "{command}" '

    # Run the command and save the output to result
    result = subprocess.run(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True)

    # Return the result
    return Result(host=task.host, result=result.stdout)

def get_ros_version(task: Task) -> Result:
    '''
    Returns the version of the routeros software running on the device.
    '''
    result = task.run(
        task=routeros_get,
        path='/system/resource',
    )

    # Parse the result to get the version (full and major)
    version = result.result[0]['version'].split(' ')[0]
    major_version = version.split('.')[0]
    task.host.data['ros_version'] = version
    task.host.data['ros_major_version'] = major_version

    return Result(
        host=task.host,
        result=version,
    )

def get_hardware(task: Task) -> Result:
    '''
    Returns the hardware type of the router (the board-name).
    '''
    result = task.run(
        task=routeros_get,
        path='/system/resource',
    )

    # Parse the result to get the version (full and major)
    hardware = result.result[0]['board-name']

    # Set the host.data dictionary to include the hardware type
    task.host.data['hardware'] = hardware

    return Result(
        host=task.host,
        result=hardware,
    )

def get_interfaces(task: Task) -> Result:
    '''
    Returns the interfaces of the router.
    '''
    result = task.run(
        task=routeros_get,
        path='/interface',
    )

    # Parse the result to get the interfaces
    interfaces = result.result

    # Set the host.data dictionary to include the interfaces
    task.host.data['interfaces'] = interfaces

    return Result(
        host=task.host,
        result=True,
    )

def get_site(task: Task) -> Result:
    '''
    Set the site in the host's data based on the name of the host.
    '''
    # Get the name of the host
    hostname = task.host.name

    # Get the site (everything preceding the first dash)
    site = hostname.split('-')[0]

    #Set the host.data dictionary to include the site
    task.host.data['site'] = site

    return Result(
        host=task.host,
        result=site,
    )

def get_role(task: Task) -> Result:
    '''
    Returns the role of the router (based on the name of the device).
    '''

    # Get the name of the host
    hostname = task.host.name

    # Get the role (everything after the first dash and before the second dash)
    role = hostname.split('-')[1].split('-')[0]

    # Remove any trailing number characters from the role (host index)
    role = role.rstrip('0123456789')
    
    # Set the host.data dictionary to include the role
    task.host.data['role'] = role

    return Result(
        host=task.host,
        result=role,
    )

def get_serial(task: Task) -> Result:
    '''
    Get the serial number of the device.
    '''
    result = task.run(
        task=routeros_get,
        path='/system/routerboard',
    )

    # Parse the result to get the serial number
    serial = result.result[0]['serial-number']

    # Set the host.data dictionary to include the serial number
    task.host.data['serial'] = serial

    return Result(
        host=task.host,
        result=serial,
    )

def get_ip_addresses(task: Task) -> Result:
    '''
    Get the IP addresses of the device.
    '''
    result = task.run(
        task=routeros_get,
        path='/ip/address',
    )

    # Parse the result to get the IP addresses
    ip_addresses = result.result

    # Set the host.data dictionary to include the IP addresses
    task.host.data['ip_addresses'] = ip_addresses

    return Result(
        host=task.host,
        result=ip_addresses,
    )

def get_vlans(task: Task) -> Result:
    '''
    Get the VLANs of the device.
    '''
    result = task.run(
        task=routeros_get,
        path='/interface/vlan',
    )

    # Parse the result to get the VLANs
    vlans = result.result

    # Set the host.data dictionary to include the VLANs
    task.host.data['vlans'] = vlans

    return Result(
        host=task.host,
        result=vlans,
    )

def get_config(task: Task) -> Result:
    '''
    Returns the configuration of the device.
    '''
    result = task.run(
        task=ssh_command,
        command='/export verbose'
    )

    # Parse the result to get the config
    config = result.result

    # Remove lines that start with '#'
    config = '\n'.join([line for line in config.split('\n') if not line.startswith('#')])

    # Save the config in the host's data dictionary
    task.host['config'] = config

    return Result(
        host=task.host,
        result=config,
    )