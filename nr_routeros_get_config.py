"""
This script gets the full configuration of the routeros device and saves it to a file.
"""

import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import *
from nr_mikrotik_baseline import get_ros_version
import subprocess
from config import *
from nr_mikrotik_general import *

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

    return Result(
        host=task.host,
        result=config,
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
        nr = nr.filter(name=target).filter(F(groups__contains='routeros'))
        print(f'filtered inventory to {target}')

    # Run tasks
    result = nr.run(
        task=get_ros_version,
    )
    print_result(result)

    result = nr.run(
        task=get_config,
    )
    print_result(result)

    # For each host in the result, save the config to a file
    for host in result.keys():
        # Get the config
        config = result[host].result

        # Save the config to a file in the CONF_DIR directory
        with open(f'{CONFIGS_DIR}/{host}.conf', 'w') as f:
            f.write(config)

if __name__ == "__main__":
    main()