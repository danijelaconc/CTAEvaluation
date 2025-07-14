#! /usr/bin/env python3

import json
import subprocess
from common import produce_prom_metric

extract_labels = ['vo', 'tapepool', 'vid', 'logicalLibrary']

cta_admin_output = subprocess.check_output(["cta-admin", "--json", "tape", "ls", "--all"])

cta_admin_output_json = json.loads(cta_admin_output)

available_space_on_tape = 0
partial_tapes_per_library_count = {}
available_space_per_library = {}

for metric in cta_admin_output_json:
    # extracting the value of the information from the tape ls cta-admin command
    capacity = int(metric['capacity'])
    occupancy = int(metric['occupancy'])
    tapepool = str(metric['tapepool'])
    logicalLibrary = str(metric['logicalLibrary'])
    vid = str(metric['vid'])
    vo = str(metric['vo'])

    # determining whether tape is empty or contains some number of bytes, calculating the available space
    if occupancy == 0:
        available_space_on_tape = capacity
    elif occupancy > 0:
        available_space_on_tape = capacity - occupancy

    # counting the number of partially filled tapes per library depending on specific individual tape capacity
    if 0 < occupancy < capacity:
        if logicalLibrary not in partial_tapes_per_library_count:
            partial_tapes_per_library_count[logicalLibrary] = 0

        partial_tapes_per_library_count[logicalLibrary] += 1

    # adding up the number of bytes per logical library to calculate total amount of available space per library 
    if logicalLibrary not in available_space_per_library:
        available_space_per_library[logicalLibrary] = 0

    available_space_per_library[logicalLibrary] += available_space_on_tape

    labels_dict = {"vo": vo, "tapepool": tapepool, "vid": vid, "logicalLibrary": logicalLibrary}

    # formatting to look like what prometheus wants
    # returns values and metrics for each individual unique tape
    #produce_prom_metric('tape_capacity', capacity, labels_dict, labels=extract_labels)
    #produce_prom_metric('tape_occupancy', occupancy, labels_dict, labels=extract_labels)
    #produce_prom_metric('tape_available_space', available_space_on_tape, labels_dict, labels=extract_labels)

# formatting for prometheus, returning total available space per logical library
for logicalLibrary, total_available_space in available_space_per_library.items():
    produce_prom_metric('tape_total_available_space', total_available_space, {"logicalLibrary": logicalLibrary}, labels=extract_labels)

# formatting for prometheus, returning number of partially filled tapes per logical library
for logicalLibrary, partially_filled_tapes in partial_tapes_per_library_count.items():
    produce_prom_metric('tape_partially_filled', partially_filled_tapes, {"logicalLibrary": logicalLibrary}, labels=extract_labels)
