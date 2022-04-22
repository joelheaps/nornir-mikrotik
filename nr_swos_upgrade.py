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

def upgrade_firmware(task: Task) -> Result:
    try:
        # Send debug message to log file
        logging.debug(f"Opening webdriver {task.host.name}")

        # Set firefox to run in headless mode
        firefox_options = webdriver.firefox.options.Options()
        firefox_options.headless = True

        # Open webdriver
        wdriver = webdriver.Firefox(options=firefox_options)
        wdriver.implicitly_wait(5)
        wdriver.get(f'http://{task.host.username}:{task.host.password}@{task.host.hostname}/index.html#upgrade')
    except Exception as e:
        
        # Send debug message to log file
        logging.debug(f"Failed to open webdriver {task.host.name}. Error: {e}")
        return Result(
            host=task.host,
            result=f"Failed to open webdriver {task.host.name}. Error: {e}",
        )

    # Begin the upgrade and log any errors
    try:
        # Send debug output to the log file
        logging.debug(f' on {task.host.name}')

        apply_button = wdriver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/div/table[1]/tbody[2]/tr[3]/td/div/a')
        apply_button.click()

        # Wait for the upgrade to complete
        wdriver.implicitly_wait(60)
    except Exception as e:
        logging.error(f'Error beginning upgrade on {task.host.name}: {e}')
        return Result(
            host=task.host,
            result=f'Error beginning upgrade on {task.host.name}: {e}',
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
        result=f'Successfully began upgrade on {task.host.name}',
    )

def main():
    # initialize Nornir
    nr = InitNornir()

    # Save the first argument passed to the script as a variable called target if sys.argv[1] exists
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # If target is 'all', continue. Otherwise, filter the inventory using target as a hostname
    if target == 'all':
        nr = nr.filter(F(groups__contains='swos'))
    else:
        nr = nr.filter(name=target).filter(F(groups__contains='swos'))
        print(f'filtered inventory to {target}')

    # Run tasks
    logging.debug('Running tasks')

    result = nr.run(
        task=upgrade_firmware,
    )
    print_result(result)

if __name__ == "__main__":
    main()