"""
This script sets the router's update branch to long-term,
downloads the latest update, enables the IPv6 package, and schedules a reboot.
"""

import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import routeros_config_item
from nornir_routeros.plugins.tasks import routeros_command
from nr_mikrotik_general import *
import datetime

def set_update_branch(task: Task) -> Result:
    '''
    Sets the Mikrotik update branch to long-term
    '''
    if task.host.data['ros_major_version'] == '6':
        task.run(
            task=routeros_config_item,
            path='/system/package/update',
            where={},
            properties={
                'channel': 'long-term',
            }
        )
    elif task.host.data['ros_major_version'] == '7':
        task.run(
            task=routeros_config_item,
            path='/system/package/update',
            where={},
            properties={
                'channel': 'stable',
            }
        )

    return Result(
        host=task.host,
        result=f"Update channel set {task.host}",
    )

def update(task: Task) -> Result:
    '''
    Check for updates and download the latest update
    '''

    task.run(
        task=routeros_command,
        path='/system/package/update',
        command='check-for-updates',
    )

    task.run(
        task=routeros_command,
        path='/system/package/update',
        command='download',
    )

    return Result(
        host=task.host,
        result=f"Update downloaded {task.host}",
    )

def enable_ipv6(task: Task) -> Result:
    '''
    Enable IPv6 package on the device
    '''
    if task.host.data['ros_major_version'] == '6':
        task.run(
            task=routeros_command,
            path='/system/package',
            command='enable',
            numbers='ipv6',
        )

    return Result(
        host=task.host,
        result=f"IPv6 package enabled {task.host}",
    )

def schedule_reboot(task: Task) -> Result:
    '''
    Schedules reboot for 3:00 AM the next day
    '''
    # Get tomorrow's date in the format MMM/DD/YYYY using datetime
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    tomorrow = tomorrow.strftime('%b/%d/%Y')

    task.run(
        task=routeros_config_item,
        path='/system/scheduler',
        where={
            'name': 'reboot-for-update',
        },
        properties={
            'name': 'reboot-for-update',
            'policy': 'reboot',
            'start-date': tomorrow,
            'start-time': '03:00:00',
            'on-event': '/system reboot',
        },
        add_if_missing=True
    )

    return Result(
        host=task.host,
        result=f"Reboot scheduled {task.host}",
    )

def main():
    # initialize Nornir
    nr = InitNornir()

    # Using the first argument passed to the script as the hostname, filter a single host from the inventory
    target = nr.filter(name=sys.argv[1]).filter(F(groups__contains='routeros'))

    # Gather info
    result = target.run(
        task=get_ros_version,
    )
    print_result(result)

    # Run tasks
    result = target.run(
        task=set_update_branch,
        name='Set update branch to long-term or stable',
    )
    print_result(result)

    result = target.run(
        task=update,
        name='Download latest update',
    )
    print_result(result)


    result = target.run(
        task=enable_ipv6,
        name='Enable IPv6 package on v6 branch',
    )
    print_result(result)

    result = target.run(
        task=schedule_reboot,
        name='Schedule reboot for 3:00 AM tomorrow',
    )
    print_result(result)

if __name__ == "__main__":
    main()