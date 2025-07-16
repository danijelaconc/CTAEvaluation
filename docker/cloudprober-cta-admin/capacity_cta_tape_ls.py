#! /usr/bin/env python3

import json
import subprocess
from common import produce_prom_metric

extract_labels = ['vo', 'tapepool', 'vid', 'logicalLibrary', 'full']

#cta_admin_output = subprocess.check_output(["cta-admin", "--json", "tape", "ls", "--all"])
cta_admin_output = subprocess.check_output(["XrdSecPROTOCOL=sss XrdSecSSSKT=/etc/cta/checkmk_sss.keytab cta-admin --json tape ls --all"], shell=True) 

cta_admin_output_json = json.loads(cta_admin_output)

available_space_on_tape = 0
partial_tapes_per_library_count = {}
enstore_partial_tapes_per_library_count = {}
available_space_per_library = {}
occupied_space_per_library = {}
fully_filled_tapes_per_library_count = {}

for metric in cta_admin_output_json:
    # extracting the value of the information from the tape ls cta-admin command
    capacity = int(metric['capacity'])
    occupancy = int(metric['occupancy'])
    tapepool = str(metric['tapepool'])
    logicalLibrary = str(metric['logicalLibrary'])
    vid = str(metric['vid'])
    vo = str(metric['vo'])
    full = str(metric['full'])

    # calculating the available space in each tape
    if occupancy == 0:
        available_space_on_tape = capacity
    else:
        available_space_on_tape = capacity - occupancy

    # counting total number of partially filled tapes per library depending on individual tape capacity
    if 0 < occupancy < (0.95*capacity):
        if logicalLibrary not in partial_tapes_per_library_count:
            # initializes value for the library if the library does not yet exist in dictionary
            partial_tapes_per_library_count[logicalLibrary] = 0
        partial_tapes_per_library_count[logicalLibrary] += 1
    
        # number of partially filled tapes for just Enstore
        if full == 'True':
            if logicalLibrary not in enstore_partial_tapes_per_library_count:
                enstore_partial_tapes_per_library_count[logicalLibrary] = 0
            enstore_partial_tapes_per_library_count[logicalLibrary] += 1

    # adding number of bytes per library for total available space per library (tapes not from Enstore)
    if full == 'False':
        if logicalLibrary not in available_space_per_library:
            # initializes value for the library if it does not yet exist in dictionary
            available_space_per_library[logicalLibrary] = 0
        available_space_per_library[logicalLibrary] += available_space_on_tape

    # adding tape occupancy for total occupied bytes per library
    if logicalLibrary not in occupied_space_per_library:
        occupied_space_per_library[logicalLibrary] = 0
    occupied_space_per_library[logicalLibrary] += occupancy

    # number of fully filled tapes per library
    if occupancy >= (0.95*capacity):
        if logicalLibrary not in fully_filled_tapes_per_library_count:
            fully_filled_tapes_per_library_count[logicalLibrary] = 0
        fully_filled_tapes_per_library_count[logicalLibrary] += 1

    labels_dict = {"vo": vo, "tapepool": tapepool, "vid": vid, "logicalLibrary": logicalLibrary, "full": full}

    # optional prometheus per-tape metrics
    #produce_prom_metric('tape_capacity', capacity, labels_dict, labels=extract_labels)
    #produce_prom_metric('tape_occupancy', occupancy, labels_dict, labels=extract_labels)
    #produce_prom_metric('tape_available_space', available_space_on_tape, labels_dict, labels=extract_labels)

# formatting for prometheus, returning total available space per library in bytes (excluding enstore tapes)
for logicalLibrary, total_available_space in available_space_per_library.items():
    produce_prom_metric('tape_library_total_available_space', total_available_space, {"logicalLibrary": logicalLibrary}, labels=["logicalLibrary"])

# number of partially filled tapes per library
for logicalLibrary, partially_filled_tapes in partial_tapes_per_library_count.items():
    produce_prom_metric('total_tapes_partially_filled', partially_filled_tapes, {"logicalLibrary": logicalLibrary}, labels=["logicalLibrary"])

# number of enstore partially filled tapes per library
for logicalLibrary, enstore_partially_filled_tapes in enstore_partial_tapes_per_library_count.items():
    produce_prom_metric('enstore_total_tapes_partially_filled', enstore_partially_filled_tapes, {"logicalLibrary": logicalLibrary}, labels=["logicalLibrary"])

# occupied space per library in bytes
for logicalLibrary, occupied_space in occupied_space_per_library.items():
    produce_prom_metric('total_occupied_space_per_library', occupied_space, {"logicalLibrary": logicalLibrary}, labels=["logicalLibrary"])

# number of fully filled tapes per library
for logicalLibrary, fully_filled_tapes in fully_filled_tapes_per_library_count.items():
    produce_prom_metric('total_fully_filled_tapes', fully_filled_tapes, {"logicalLibrary": logicalLibrary}, labels=["logicalLibrary"])
