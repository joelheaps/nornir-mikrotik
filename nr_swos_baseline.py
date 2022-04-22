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
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging

logging.basicConfig(filename='logs/nr_swos_snmp.log', level=logging.DEBUG)

def get_site(task: Task) -> Result:
    # Set the site in the host.data dictionary to the substring preceding the first dash in the host's name
    task.host.data['site'] = task.host.name.split('-')[0]
    logging.debug(f'Set site to {task.host.data["site"]}')

    return Result(
        host=task.host,
        result=f"Site: {task.host.data['site']}",
    )

def configure_snmp(task: Task) -> Result:
    try:
        # Send debug message to log file
        logging.debug(f"Opening webdriver {task.host.name}")
        wdriver = webdriver.Firefox()
        wdriver.implicitly_wait(5)
        wdriver.get(f'http://{task.host.username}:{task.host.password}@{task.host.hostname}/index.html#snmp')
    except Exception as e:
        # Send debug message to log file
        logging.debug(f"Failed to open webdriver {task.host.name}. Error: {e}")
        return Result(
            host=task.host,
            result=f"Failed to open webdriver {task.host.name}. Error: {e}",
        )

    # Configure SNMP and log any errors
    try:
        # Send debug output to the log file
        logging.debug(f'Configuring SNMP on {task.host.name}')

        # Enable SNMP checkbox
        enabled_button = wdriver.find_element(By.ID, 'en0')
        if not enabled_button.is_selected():
            enabled_button.click()

        # Set SNMP community
        community_input = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/input')
        community_input.clear()
        community_input.send_keys(SNMP_COMMUNITY)

        # Set SNMP contact
        contact_input = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table/tbody/tr[3]/td/input')
        contact_input.clear()
        contact_input.send_keys(SNMP_CONTACT)

        # Set SNMP location
        location_input = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table/tbody/tr[4]/td/input')
        location_input.clear()
        location_input.send_keys(task.host.data['site'])
    except Exception as e:
        logging.error(f'Error configuring SNMP on {task.host.name}: {e}')
        return Result(
            host=task.host,
            result=f'Error configuring SNMP on {task.host.name}: {e}',
        )

    # Apply the changes and log any errors
    try:
        # Send debug output to the log file
        logging.debug(f'Applying SNMP changes on {task.host.name}')

        apply_button = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table/tbody/tr[5]/td/div/div/a[1]')
        apply_button.click()
    except Exception as e:
        logging.error(f'Error applying SNMP changes to {task.host.name}: {e}')
        return Result(
            host=task.host,
            result=f'Error applying SNMP changes to {task.host.name}: {e}',
        )

    # Close the webdriver
    try:
        # Send debug output to the log file
        logging.debug(f'Closing webdriver {task.host.name}')
        wdriver.close()
    except:
        logging.error(f'Error closing webdriver {task.host.name}')
        return Result(
            host=task.host,
            result=f'Error closing webdriver {task.host.name}',
        )

    # Return a result with the success status
    return Result(
        host=task.host,
        result=f'Successfully configured SNMP on {task.host.name}',
    )

def set_identity(task: Task) -> Result:
    # Open the webdriver to the system page
    try:
        # Send debug message to log file
        logging.debug(f"Opening webdriver {task.host.name}")
        wdriver = webdriver.Firefox()
        wdriver.implicitly_wait(5)
        wdriver.get(f'http://{task.host.username}:{task.host.password}@{task.host.hostname}/index.html#system')
    except Exception as e:
        # Send debug message to log file
        logging.debug(f"Failed to open webdriver {task.host.name}. Error: {e}")
        return Result(
            host=task.host,
            result=f"Failed to open webdriver {task.host.name}. Error: {e}",
        )

    # Configure SNMP and log any errors
    try:
        # Send debug output to the log file
        logging.debug(f'Configuring SNMP on {task.host.name}')

        # Set the identity
        identity_input = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table[1]/tbody/tr[3]/td/input')
        identity_input.clear()
        identity_input.send_keys(task.host.name)
    except Exception as e:
        logging.error(f'Error configuring identity on {task.host.name}: {e}')
        return Result(
            host=task.host,
            result=f'Error configuring identity on {task.host.name}: {e}',
        )

    # Apply the changes and log any errors
    try:
        # Send debug output to the log file
        logging.debug(f'Applying changes on {task.host.name}')

        apply_button = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table/tbody/tr[5]/td/div/div/a[1]')
        apply_button.click()
    except Exception as e:
        logging.error(f'Error applying changes on {task.host.name}: {e}')
        return Result(
            host=task.host,
            result=f'Error applying changes on {task.host.name}: {e}',
        )

    # Close the webdriver
    try:
        # Send debug output to the log file
        logging.debug(f'Closing webdriver {task.host.name}')
        wdriver.close()
    except:
        logging.error(f'Error closing webdriver {task.host.name}')
        return Result(
            host=task.host,
            result=f'Error closing webdriver {task.host.name}',
        )

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
        task=configure_snmp,
    )
    print_result(result)

if __name__ == "__main__":
    main()