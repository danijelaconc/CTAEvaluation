import json
import subprocess
from common import produce_prom_metric

extract_labels = ['vo', 'tapepool', 'vid', 'logicalLibrary']

cta_admin_output = subprocess.check_output(["cta-admin", "--json", "tape", "ls", "--all"])

cta_admin_output_json = json.loads(cta_admin_output)

available_space_on_tape = 0

for metric in cta_admin_output_json:
    # extracting the value of the information from the tape ls cta-admin command
    capacity = int(metric['capacity'])
    occupancy = int(metric['occupancy'])
    tapepool = str(metric['tapepool'])
    logicalLibrary = str(metric['logicalLibrary'])
    vid = str(metric['vid'])
    vo = str(metric['vo'])

    if occupancy == 0:
        available_space_on_tape = capacity
    elif occupancy > 0:
        available_space_on_tape = capacity - occupancy

    labels_dict = {"vo": vo, "tapepool": tapepool, "vid": vid, "logicalLibrary": logicalLibrary}

    # formatting to look like what prometheus wants
    produce_prom_metric('tape_capacity', capacity, labels_dict, labels=extract_labels)
    produce_prom_metric('tape_occupancy', occupancy, labels_dict, labels=extract_labels)
    produce_prom_metric('tape_available_space', available_space_on_tape, labels_dict, labels=extract_labels)
