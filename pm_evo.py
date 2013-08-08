#!/usr/bin/env tdaq_python

from pm.project import Project
import argparse
from pprint import pprint
from pm_ros import create_ros_segment
from pm_common import (create_config_rules,
                       create_template_applications, INCLUDES)
from pm_hltsv import create_hlt_segment, add_dcm_segments
from pm_hlt import create_dcm_segment
from pm_partition import create_partition

def create_config_db(args):
    hlt_segments = []
    part_segments = []
    exec("from " + args.farm_file + " import farm_dict")
    
    farm_dict['name'] = args.partition_name
    repository_root = args.repository_root
    data_networks = args.data_networks
    multicast_address = args.multicast_address

    full_includes = INCLUDES + args.extra_includes
    db = Project(farm_dict['name'] + ".data.xml", full_includes)
    if args.local:
        lh = farm_dict['default_host']
        for iface in lh.Interfaces:
            db.updateObjects([iface])
            
        db.updateObjects([lh])
    
    create_config_rules(db)
    create_template_applications(db, args.dcm_only, args.hltpu_only)

    for dcm in farm_dict['dcms']:
        dcm['hltpu_only'] = args.hltpu_only
        dcm['dcm_only'] = args.dcm_only
        dcm['db'] = db
        dcm_segment = create_dcm_segment(**dcm)
        hlt_segments.append(dcm_segment)

    hlt_segment = (create_hlt_segment(db, farm_dict['default_host'],
                                      farm_dict['hltsv'], farm_dict['sfos']))
    add_dcm_segments(db, hlt_segments)
    part_segments.append(hlt_segment)
    
    ros_segment = create_ros_segment(db)
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

    create_partition(**part_params)
    

def main():
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
    args = parser.parse_args()
    pprint(args)
    create_config_db(args)

if __name__ == '__main__':
    main()
    
    
