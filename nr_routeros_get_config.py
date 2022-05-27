"""
This script gets the full configuration of the routeros device,
saves it to a git repository, makes a commit, and pushes the changes to the remote repository.
"""

import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import *
import subprocess
from config import *
from nr_routeros_general import *
import datetime

def find_config_and_commit(task: Task) -> Result:
    '''
    Saves the configuration to a file and commits it to the git repository.
    Store config temporarily in CONFIGS_DIR/staging.  If the config is different than
    the old config, move it to CONFIGS_DIR and make a commit.
    '''
    # Get the config.  If the config is None or empty, return an error.
    try:
        result = task.run(
            task=get_config,
        )
        print_result(result)

        config = task.host.data['config']

        if config is None or config == '':
            raise Exception('config is empty')

    except Exception as e:
        print(f'{task.host} failed to get config: {e}')
        return Result(
            host=task.host,
            result=None,
        )

    # Save the config to a file in the CONFIGS_DIR/staging directory
    with open(f'{CONFIGS_DIR}/staging/{task.host.name}.rsc', 'w') as f:
        f.write(config)

    # Read the old config from the CONFIGS_DIR directory. Check if the file exists first.
    try:
        with open(f'{CONFIGS_DIR}/{task.host.name}.rsc', 'r') as f:
            old_config = f.read()
    except FileNotFoundError:
        old_config = ''

    # Compare the new config with the old config. If they are different, move the new config to the CONFIGS_DIR directory
    # and make a commit.
    if config != old_config:
        # Get current date and time in a readable format
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # Move the new config to the CONFIGS_DIR directory
        subprocess.run(f'mv {CONFIGS_DIR}/staging/{task.host.name}.rsc {CONFIGS_DIR}/{task.host.name}.rsc', shell=True)

        # Make a commit
        subprocess.run(f'cd {CONFIGS_DIR} && git add {task.host.name}.rsc && git commit -m "config updated on {task.host.name} at {now}"', shell=True)

    return Result(
        host=task.host,
        result=f'Successfully committed config for {task.host.name}',
    )

def push_config():
    '''
    Push config from local master to remote origin repository.
    '''
    subprocess.run(f'cd {CONFIGS_DIR} && git push origin master', shell=True)

def main():
    # initialize Nornir
    nr = InitNornir()

    # Save the first argument passed to the script as a variable called target if sys.argv[1] exists
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # If target is 'all', continue. Otherwise, filter the inventory using target as a hostname
    if target == 'all':
        nr = nr.filter(F(groups__contains='routeros'))
    else:
        nr = nr.filter(name=target).filter(F(groups__contains='routeros'))
        print(f'filtered inventory to {target}')

    # Run tasks
    ros_version_result = nr.run(
        task=get_ros_version,
    )
    print_result(ros_version_result)

    config_result = nr.run(
        task=find_config_and_commit,
    )
    print_result(config_result)

    # Print a bulleted list of hosts for which tasks failed
    for host in ros_version_result.failed_hosts:
        print(f'- {host}: failed to connect or get ROS version')

    # Push config to remote repository
    try:
        push_config()
        print('config pushed to remote repository')
    except Exception as e:
        print(f'failed to push config: {e}')

if __name__ == "__main__":
    main()