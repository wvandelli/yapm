from pm.project import Project
import argparse
import pm_ros
import pm_common
import pm_hltsv
import pm_hlt
import pm_partition
import imp

DEFAULT_INCLUDES = ['daq/hw/hosts.data.xml',
                    'daq/segments/setup.data.xml',
                    'daq/schema/hltsv.schema.xml',
                    'daq/schema/HLTMPPU.schema.xml',
                    'daq/sw/repository.data.xml',
                    'daq/schema/dcm.schema.xml',
                    'daq/sw/tags.data.xml',
                    'daq/sw/common-templates.data.xml'
                    ]

def get_post_process(module_name):
    post_process = imp.find_module(module_name)
    post_process_module = imp.load_module(module_name, post_process[0], post_process[1],
                                          post_process[2])
    return post_process_module.modify

def post_process(args, config_db):
    if not args.post_processor: return 
    modify = get_post_process(args.post_processor)
    hlt_segment = modify(config_db)

    return hlt_segment

def get_farm_dict(module_name):
    farm_gen = imp.find_module(module_name)
    farm_gen_mod = imp.load_module(module_name, farm_gen[0], farm_gen[1],
                                   farm_gen[2])

    return farm_gen_mod.farm_dict

def create_config_db(args):
    hlt_segments = []
    farm_dict = get_farm_dict(args.farm_file)
    print("got farm_dict")
    

    full_includes = DEFAULT_INCLUDES + args.extra_includes
    
    config_db = Project("HLT.data.xml", full_includes)
    if args.local:
        local_host = farm_dict['default_host']
        for iface in local_host.Interfaces:
            config_db.updateObjects([iface])

        config_db.updateObjects([local_host])

    pm_common.create_config_rules(config_db)
    pm_common.create_template_applications(config_db, args.dcm_only,
                                           args.hltpu_only, farm_dict['sfos'])

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
    post_process(args, config_db)
    


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--farm-file",
                        help='Farm that contains dictionary',
                        required=True)
    parser.add_argument("-I", "--extra-includes", nargs='+',
                        help='Add include files',
                        required=False, type=str, default=[])
    parser.add_argument("--dcm-only", required=False, default=False,
                        action="store_true")
    parser.add_argument("--hltpu-only", required=False, default=False,
                        action="store_true")
    parser.add_argument("--local", required=False, default=False,
                        action="store_true")
    parser.add_argument("-z", "--post-processor", required=False,
                        default=None)

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



