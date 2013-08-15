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
import pm_ros
import pm_common
import pm_hltsv
import pm_hlt
import pm_partition
import imp

IMPORT_ERROR_MESSAGE = "Couldn't import module provided: %s"
ATTR_ERROR_MESSAGE = (
                     """
                     Couldn't find dictionary with
                     default name(farm_dict) in module provided"
                     """
                     )

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

    full_includes = pm_common.DEFAULT_INCLUDES + args.extra_includes
    config_db = Project(args.partition_name + ".data.xml", full_includes)
    print "created file"
    if args.local:
        local_host = farm_dict['default_host']
        for iface in local_host.Interfaces:
            config_db.updateObjects([iface])

        config_db.updateObjects([local_host])

    pm_common.create_config_rules(config_db)
    pm_common.create_default_gatherer_options(config_db)
    pm_common.create_template_applications(config_db, args.dcm_only,
                                           args.hltpu_only)

    for dcm in farm_dict['dcms']:
        dcm['hltpu_only'] = args.hltpu_only
        dcm['dcm_only'] = args.dcm_only
        dcm['config_db'] = config_db
        dcm_segment = pm_hlt.create_dcm_segment(**dcm)
        hlt_segments.append(dcm_segment)

    hlt_segment = (pm_hltsv.create_hlt_segment(config_db,
                                               farm_dict['default_host'],
                                               farm_dict['hltsv'],
                                               farm_dict['sfos']))
    pm_hltsv.add_dcm_segments(config_db, hlt_segments)
    part_segments.append(hlt_segment)

    #ros_segment = pm_ros.create_ros_segment(config_db)
    #part_segments.append(ros_segment)

    part_params = {
                   'config_db'         : config_db,
                   'part_name'         : args.partition_name,
                   'repository_root'   : args.repository_root,
                   'segments'          : part_segments,
                   'data_networks'     : args.data_networks,
                   'multicast_address' : args.multicast_address,
                   'default_host'      : farm_dict['default_host']
                   }

    pm_partition.create_partition(**part_params)

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
