"""
This script sets baseline configuration on routers, including:
- Configure NTP client
- Configure SNMP communities
- Configure remote logging
- Create a 'netauto' user
"""

import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import *
from nr_mikrotik_general import *

def configure_ntp(task: Task) -> Result:
    '''
    Enables and configures NTP client on the device.
    
    Reference configuration:
    /system ntp client
    set enabled=yes primary-ntp=5.145.135.89 secondary-ntp=94.16.122.254 \
    server-dns-names=0.pool.ntp.org,1.pool.ntp.org
    '''
    if task.host.data['ros_major_version'] == '6':
        task.run(
            task=routeros_config_item,
            path='/system/ntp/client',
            where={},
            properties={
                'enabled': 'yes',
                'server-dns-names': '0.pool.ntp.org,1.pool.ntp.org',
            }
        )
    elif task.host.data['ros_major_version'] == '7':
        task.run(
            task=routeros_config_item,
            path='/system/ntp/client/servers',
            where={
                'address': 'pool.ntp.org'
            },
            properties={
                'address': 'pool.ntp.org',
            },
            add_if_missing=True
        )

        task.run(
            task=routeros_config_item,
            path='/system/ntp/client',
            where={},
            properties={
                'enabled': 'yes',
            }
        )

    return Result(
        host=task.host,
        result=f"NTP enabled and configured on {task.host}",
    )

def configure_snmp(task: Task) -> Result:
    '''
    Enables and configures SNMP on the device.
    
    Reference configuration:
    /snmp community
    set [ find default=yes ] disabled=yes
    add addresses={TRUSTED_ADDRESSES} authentication-password=\
    {SNMP_COMMUNITY} encryption-password={SNMP_COMMUNITY} encryption-protocol=AES \
    name={SNMP_COMMUNITY} security=private

    /snmp
    set contact={SNMP_CONTACT} enabled=yes location={site}
    '''
    
    # Set site as string preceding first '-' in hostname
    site = str(task.host).split('-')[0]

    task.run(
        task=routeros_config_item,
        path='/snmp/community',
        where={
            'name': f'{SNMP_COMMUNITY}',
        },
        properties={
            'name': f'{SNMP_COMMUNITY}',
            'authentication-password': f'{SNMP_COMMUNITY}',
            'authentication-protocol': 'MD5',
            'encryption-password': f'{SNMP_COMMUNITY}',
            'encryption-protocol': 'AES',
            'security': 'private',
            'addresses': TRUSTED_ADDRESSES
        },
        add_if_missing=True
    )

    task.run(
        task=routeros_config_item,
        path='/snmp',
        where={},
        properties={
            'contact': 'admin@wiaw.net',
            'enabled': 'yes',
            'location': site,
        }
    )

    return Result(
        host=task.host,
        result=f"SNMP enabled and configured on {task.host}",
    )

def configure_remote_logging(task: Task) -> Result:
    '''
    Enables and configures remote logging on the device.
    
    Reference configuration:
    /system logging action
    set 3 bsd-syslog=no name=remote remote={REMOTE_LOGGING_TARGET} remote-port=514 \
        src-address={task.host.hostname} syslog-facility=daemon syslog-severity=auto \
        syslog-time-format=bsd-syslog target=remote

    /system logging
    add action=remote disabled=no prefix="" topics=critical
    add action=remote disabled=no prefix="" topics=info
    add action=remote disabled=no prefix="" topics=error
    add action=remote disabled=no prefix="" topics=warning
    '''

    task.run(
        task=routeros_config_item,
        name='Create logging action',
        path='/system/logging/action',
        where={
            'name': 'remote',
        },
        properties={
            'remote': REMOTE_LOGGING_TARGET,
            'remote-port': '514',
            'src-address': f'{task.host.hostname}',
            'syslog-facility': 'daemon',
            'syslog-severity': 'auto',
            'syslog-time-format': 'bsd-syslog',
            'target': 'remote',
        }
    )

    task.run(
        task=routeros_config_item,
        name='Create critical logging action',
        path='/system/logging',
        where={
            'topics': 'critical',
            'action': 'remote',
        },
        properties={
            'topics': 'critical',
            'action': 'remote',
            'disabled': 'no',
        },
        add_if_missing=True
    )

    task.run(
        task=routeros_config_item,
        name='Create info logging action',
        path='/system/logging',
        where={
            'topics': 'info',
            'action': 'remote',
        },
        properties={
            'topics': 'info',
            'action': 'remote',
            'disabled': 'no',
        },
        add_if_missing=True
    )

    task.run(
        task=routeros_config_item,
        name='Create error logging action',
        path='/system/logging',
        where={
            'topics': 'error',
            'action': 'remote',
        },
        properties={
            'topics': 'error',
            'action': 'remote',
            'disabled': 'no',
        },
        add_if_missing=True
    )

    task.run(
        task=routeros_config_item,
        name='Create warning logging action',
        path='/system/logging',
        where={
            'topics': 'warning',
            'action': 'remote',
        },
        properties={
            'topics': 'warning',
            'action': 'remote',
            'disabled': 'no',
        },
        add_if_missing=True
    )

    return Result(
        host=task.host,
        result=f"Remote logging enabled and configured on {task.host}",
    )

def configure_ip_services(task: Task) -> Result:
    '''
    This task configures IP services and their access rules on the device.

    Reference config:
    /ip service
    set telnet disabled=yes
    set ftp disabled=yes
    set www disabled=yes
    set ssh address={TRUSTED_ADDRESSES} disabled=no
    set api address={TRUSTED_ADDRESSES} disabled=no
    set winbox address={TRUSTED_ADDRESSES} disabled=no
    set api-ssl disabled=yes
    '''

    # Configure telnet
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'telnet',
        },
        properties={
            'disabled': 'yes',
        },
    )

    # Configure ftp
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'ftp',
        },
        properties={
            'disabled': 'yes',
        },
    )

    # Configure www
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'www',
        },
        properties={
            'disabled': 'yes',
        },
    )

    # Configure ssh
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'ssh',
        },
        properties={
            'address': TRUSTED_ADDRESSES,
            'disabled': 'no',
        },
    )

    # Configure api
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'api',
        },
        properties={
            'address': TRUSTED_ADDRESSES,
            'disabled': 'no',
        },
    )

    # Configure winbox
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'winbox',
        },
        properties={
            'address': TRUSTED_ADDRESSES,
            'disabled': 'no',
        },
    )

    # Configure api-ssl
    task.run(
        task=routeros_config_item,
        path='/ip/service',
        where={
            'name': 'api-ssl',
        },
        properties={
            'disabled': 'yes',
        },
    )

    return Result(
        host=task.host,
        result=f"IP services and access rules configured on {task.host}",
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
        task=configure_ntp,
    )
    print_result(result)

    result = nr.run(
        task=configure_snmp,
    )
    print_result(result)

    result = nr.run(
        task=configure_remote_logging,
    )
    print_result(result)

    result = nr.run(
        task=configure_ip_services,
    )
    print_result(result)

if __name__ == "__main__":
    main()