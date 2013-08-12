#!/usr/bin/env tdaq_python

from pm.project import Project
import argparse
from pprint import pprint
import pm_ros
import pm_common
import pm_hltsv 
import pm_hlt 
import pm_partition

def create_config_db(args):
    hlt_segments = []
    part_segments = []
    exec("from " + args.farm_file + " import farm_dict")
    
    farm_dict['name'] = args.partition_name
    repository_root = args.repository_root
    data_networks = args.data_networks
    multicast_address = args.multicast_address

    full_includes = pm_common.INCLUDES + args.extra_includes
    db = Project(farm_dict['name'] + ".data.xml", full_includes)
    if args.local:
        lh = farm_dict['default_host']
        for iface in lh.Interfaces:
            db.updateObjects([iface])
            
        db.updateObjects([lh])
    
    pm_common.create_config_rules(db)
    pm_common.create_default_gatherer_options(db)
    pm_common.create_template_applications(db, args.dcm_only, args.hltpu_only)
    
    for dcm in farm_dict['dcms']:
        dcm['hltpu_only'] = args.hltpu_only
        dcm['dcm_only'] = args.dcm_only
        dcm['db'] = db
        dcm_segment = pm_hlt.create_dcm_segment(**dcm)
        hlt_segments.append(dcm_segment)

    hlt_segment = (pm_hltsv.create_hlt_segment(db, farm_dict['default_host'],
                                               farm_dict['hltsv'],
                                               farm_dict['sfos']))
    pm_hltsv.add_dcm_segments(db, hlt_segments)
    part_segments.append(hlt_segment)
    
    ros_segment = pm_ros.create_ros_segment(db)
    part_segments.append(ros_segment)
    
    part_params = {
                   'db'       : db, 
                   'part_name': farm_dict['name'],
                   'repository_root': repository_root,
                   'segments': part_segments,
                   'data_networks':data_networks,
                   'multicast_address':multicast_address,
                   'default_host': farm_dict['default_host']
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
    pprint(args)

    if args.hltpu_only and args.dcm_only:
        print("Incompatible options hltpu-only and dcm-only.")
        return
    
    create_config_db(args)
    
if __name__ == '__main__':
    command_line_runner()
    
    
