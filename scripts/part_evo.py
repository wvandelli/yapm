"""
This module creates a complete partition in a bottom up approach
according to the farm description it loads from the file provided as
command-line argument and the other command line arguments. Starts
from the standalone hlt segments which don't contain any other
segments and then moves up to the top level segments(HLTSV, ROS) and
then finally to the partition object.  No error checking yet on the
sanity of the provided command line arguments and the farm dictionary
"""

from pm.project import Project
import argparse
import yapm.ros
import yapm.common
import yapm.hltsv
import yapm.hlt
import yapm.partition
import imp

IMPORT_ERROR_MESSAGE = "Couldn't import module provided: %s"
ATTR_ERROR_MESSAGE = "Couldn't find dictionary with default name(farm_dict) in module provided"

DEFAULT_INCLUDES = ['daq/hw/hosts.data.xml',
                    'daq/segments/setup.data.xml',
                    'daq/schema/hltsv.schema.xml',
                    'daq/schema/HLTMPPU.schema.xml',
                    'daq/schema/SFOng.schema.xml',
                    'daq/sw/repository.data.xml',
                    'daq/schema/dcm.schema.xml',
                    'daq/sw/tags.data.xml',
                    'daq/sw/common-templates.data.xml'
                    ]

def get_farm_dict(module_name):
    farm_gen = imp.find_module(module_name)
    farm_gen_mod = imp.load_module(module_name, farm_gen[0], farm_gen[1],
                                   farm_gen[2])

    return farm_gen_mod.farm_dict

def create_config_db(args):
    hlt_segments = []
    part_segments = []
    try:
        farm_dict = get_farm_dict(args.farm_file)
    except ImportError:
        print(IMPORT_ERROR_MESSAGE % args.farm_file)
        return
    except AttributeError:
        print(ATTR_ERROR_MESSAGE)
        return

    full_includes = DEFAULT_INCLUDES + args.extra_includes
    config_db = Project("data/" + args.partition_name + ".data.xml", full_includes)

    if args.local:
        local_host = farm_dict['default_host']
        for iface in local_host.Interfaces:
            config_db.updateObjects([iface])

        config_db.updateObjects([local_host])

    yapm.common.create_config_rules(config_db)
    templ_apps = yapm.common.create_template_applications(config_db, args.dcm_only,
                                                          args.hltpu_only,
                                                          farm_dict['sfos'])
    for dcm in farm_dict['hlts']:
        dcm['config_db'] = config_db
        dcm['templ_apps'] = templ_apps
        dcm_segment = yapm.hlt.create_hlt_segment(**dcm)
        hlt_segments.append(dcm_segment)

    hlt_segment = (yapm.hltsv.create_hltsv_segment(config_db,
                                                   farm_dict['default_host'],
                                                   farm_dict['hltsv'],
                                                   farm_dict['sfos'],
                                                   hlt_segments))
    part_segments.append(hlt_segment)
    
    part_params = {
                   'config_db'         : config_db,
                   'part_name'         : args.partition_name,
                   'repository_root'   : args.repository_root,
                   'segments'          : part_segments,
                   'data_networks'     : args.data_networks,
                   'multicast_address' : args.multicast_address,
                   'default_host'      : farm_dict['default_host']
                   }
    
    part = yapm.partition.create_partition(**part_params)
    config_db.addObjects([part])

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--farm-file",
                        help='Farm that contains dictionary',
                        required=True)
    parser.add_argument("-D", "--data-networks", help='Data Networks',
                        required=False, type=str, nargs='+', default=[])
    parser.add_argument("-m", "--multicast-address", help='Multicast address',
                        required=False, type=str, default="")
    parser.add_argument("-I", "--extra-includes", nargs='+',
                        help='Add include files',
                        required=False, type=str, default=[])
    parser.add_argument("-r", "--repository-root", help='Repository root',
                        required=False, type=str, default="")
    parser.add_argument("--dcm-only", required=False, default=False,
                        action="store_true")
    parser.add_argument("--hltpu-only", required=False, default=False,
                        action="store_true")
    parser.add_argument("--local", required=False, default=False,
                        action="store_true")
    parser.add_argument("-p", "--partition-name", required=False,
                        default="az_test")
    return parser

def command_line_runner():
    parser = get_parser()
    args = parser.parse_args()

    if args.hltpu_only and args.dcm_only:
        print("Incompatible options hltpu-only and dcm-only.")
        return

    create_config_db(args)

if __name__ == '__main__':
    command_line_runner()
