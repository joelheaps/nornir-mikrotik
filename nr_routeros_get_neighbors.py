"""
This script gets a list of all IP neighbors from each router and dumps them to a CSV file.
"""

from cgi import print_arguments
import sys
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_routeros.plugins.tasks import *
from nr_routeros_general import *
from shlex import shlex
import logging
import json

logging.basicConfig(filename='logs/nr_mikrotik_get_neighbors.py', level=logging.DEBUG)

NEIGHBOR_ESSENTIAL_FIELDS = [
    'mac-address',
    'address',
    'identity',
    'platform',
    'version',
    'board',
    'neighbor-of',
    'interface',
]

def parse_key_value_pairs(text):
    '''
    Parse key-value pairs from a shell-like text.
    Returns a dictionary of key-value pairs.
    '''

    lexer = shlex(text, posix=True)
    lexer.whitespace_split = True

    return_dict = {}

    for key_value_pair in lexer:
        logging.debug(f'Processing key_value_pair: {key_value_pair}')

        try:
            key, value = key_value_pair.split('=', 1)
            return_dict[key] = value
        except:
            logging.error(f'Error parsing key_value_pair: {key_value_pair}')
            pass

    return return_dict

def parse_neighbors_to_dict(neighbors, neighbor_of=None):
    '''
    Parse the raw neighbors output from get_neighbors() to a dictionary.
    '''
    # Initialize empty dictionary
    neighbors_dict = {}

    # Split the raw neighbors output into a list of neighbor entries separated by a blank line
    neighbor_entries = neighbors.split('\n\n')

    # Process each neighbor entry
    for neighbor_entry in neighbor_entries:

        # If neighbor_entry is empty or contains only whitespace, skip it
        if not neighbor_entry or neighbor_entry.isspace():
            continue

        # Debug neighbor_entry
        logging.info(f'Processing neighbor_entry on {neighbor_of}: {neighbor_entry}')

        # Remove preceding space
        neighbor_entry = neighbor_entry.lstrip()

        # Create a new string without the preceding index number
        neighbor_entry = neighbor_entry.split(' ', 1)[1]

        # Split key-value pairs separated by a space, respecting quoted strings.
        # Returns list of dictionaries.
        key_value_pairs = parse_key_value_pairs(neighbor_entry)

        # Initialize empty dictionary
        neighbor_dict = {}

        # For each key-value pair, add the key and value to the neighbor_dict
        for key in key_value_pairs.keys():
            neighbor_dict[key] = key_value_pairs[key]

        # Set the neighbor_of field to the neighbor_of parameter
        neighbor_dict['neighbor-of'] = str(neighbor_of)

        # Ensure each field in NEIGHBOR_ESSENTIAL_FIELDS is present in the dictionary. Set to empty string if not present.
        for field in NEIGHBOR_ESSENTIAL_FIELDS:
            if field not in neighbor_dict.keys():
                neighbor_dict[field] = ''

        # Add this neighbor_dict to the neighbors_dict, indexed by the address
        neighbors_dict[neighbor_dict['address']] = neighbor_dict

    return neighbors_dict

def get_neighbors(task: Task) -> Result:
    '''
    Returns a list of IP neighbors by executing an SSH command.  Returns a dictionary of neighbors.
    '''
    result = task.run(
        task=ssh_command,
        command='/ip neighbor print detail without-paging'
    )
    print_result(result)

    # Parse the result to get the neighbors
    neighbors = result.result

    # Parse the neighbors to a dictionary
    neighbors_dict = parse_neighbors_to_dict(neighbors, neighbor_of=task.host)

    return Result(
        host=task.host,
        result=neighbors_dict,
    )

def main():
    # initialize Nornir
    nr = InitNornir()

    # Save the first argument passed to the script as a variable called target
    target = sys.argv[1]

    # If target is 'all', continue. Otherwise, filter the inventory using target as a hostname
    if target == 'all':
        pass
    else:
        nr = nr.filter(name=target).filter(F(groups__contains='routeros'))
        print(f'filtered inventory to {target}')

    # Run tasks
    result = nr.run(
        task=get_neighbors,
    )

    # Define an all_neighbors dictionary
    all_neighbors = {}

    # For each host in the result, save the neighbors to the all_neighbors dictionary
    for host in result.keys():
        # Get the neighbors
        neighbors = result[host].result

        # For each neighbor, add the neighbor to the all_neighbors dictionary
        for neighbor in neighbors.keys():
            all_neighbors[neighbor] = neighbors[neighbor]

    # Write the neighbors to a CSV file
    with open('neighbors.csv', 'w') as f:
        # Write CSV header based on the NEIGHBOR_ESSENTIAL_FIELDS list
        f.write(','.join(NEIGHBOR_ESSENTIAL_FIELDS) + '\n')

        for neighbor in all_neighbors.keys():

            # Include all fields in NEIGHBOR_ESSENTIAL_FIELDS in the neighbor line
            neighbor_line = ','.join([
                all_neighbors[neighbor][field] for field in NEIGHBOR_ESSENTIAL_FIELDS
            ])
            f.write(f'{neighbor_line}\n')

if __name__ == "__main__":
    main()