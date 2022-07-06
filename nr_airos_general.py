#!/usr/bin/python3
"""
Configures SNMP and system identity on switchOS devices.
"""

import sys # for catching arugments
from nornir import InitNornir
from nornir_routeros.plugins.tasks import *
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir.core.filter import F
from config import *
from nr_routeros_general import *
import logging

logging.basicConfig(filename='logs/nr_airos.log', level=logging.DEBUG)

def get_config(task: Task) -> Result:
    result = task.run(
        task=ssh_command,
        command='cat /tmp/system.cfg'
    )

    # Parse the result to get the config
    config = result.result

    # Save the config in the host's data dictionary
    task.host.data['config'] = config

    return Result(
        host=task.host,
        result=f'Successfully retrieved config for {task.host.name}',
    )

def configure_snmp(task: Task) -> Result:
    

def set_identity(task: Task) -> Result:


    # Return a result with the success status
    return Result(
        host=task.host,
        result=f'Successfully configured SNMP on {task.host.name}',
    )

def main():
    # initialize Nornir
    nr = InitNornir()

    # Save the first argument passed to the script as a variable called target if sys.argv[1] exists
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # If target is 'all', continue. Otherwise, filter the inventory using target as a hostname
    if target == 'all':
        pass
    else:
        nr = nr.filter(name=target).filter(F(groups__contains='swos'))
        print(f'filtered inventory to {target}')

    # Run tasks
    logging.debug('Running tasks')
    result = nr.run(
        task=get_site,
    )
    print_result(result)

    result = nr.run(
        task=get_config,
    )
    print_result(result)

if __name__ == "__main__":
    main()
