from pm.project import Project
import argparse
import yapm.ros
import yapm.common
import yapm.hltsv
import yapm.hlt
import yapm.partition
import imp
import time
from pprint import pprint
import sys

DEFAULT_INCLUDES = ['daq/hw/hosts.data.xml',
                    'daq/segments/setup.data.xml',
                    'daq/schema/hltsv.schema.xml',
                    'daq/schema/HLTMPPU.schema.xml',
                    'daq/sw/repository.data.xml',
                    'daq/schema/dcm.schema.xml',
                    'daq/sw/tags.data.xml',
                    'daq/sw/common-templates.data.xml'
                    ]
IMPORT_ERROR_MESSAGE = "Couldn't import module provided: %s"
ATTR_ERROR_MESSAGE = "Couldn't find dictionary with default name(farm_dict) in module provided"

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
    try:
        farm_dict = get_farm_dict(args.farm_file)
    except ImportError:
        print(IMPORT_ERROR_MESSAGE % args.farm_file)
        return
    except AttributeError:
        print(ATTR_ERROR_MESSAGE)
        return
    #farm_dict = get_farm_dict(args.farm_file)

    s_time = time.time()
    full_includes = DEFAULT_INCLUDES + args.extra_includes
    
    config_db = Project("data/HLT.data.xml", full_includes)
    if args.local:
        local_host = farm_dict['default_host']
        for iface in local_host.Interfaces:
            config_db.updateObjects([iface])

        config_db.updateObjects([local_host])

    yapm.common.create_config_rules(config_db)
    templ_apps = yapm.common.create_template_applications(config_db, args.dcm_only,
                                                          args.hltpu_only,
                                                          farm_dict['sfos'])
    for dcm in farm_dict['dcms']:
        dcm['config_db'] = config_db
        dcm['templ_apps'] = templ_apps
        dcm_segment = yapm.hlt.create_dcm_segment(**dcm)
        hlt_segments.append(dcm_segment)

    hlt_segment = (yapm.hltsv.create_hlt_segment(config_db,
                                               farm_dict['default_host'],
                                               farm_dict['hltsv'],
                                               farm_dict['sfos'],
                                               hlt_segments))
    config_db.addObjects([hlt_segment])
    print(time.time() - s_time)
    post_process(args, config_db)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--farm-file",
                        help='Python module that contains a dictionary that contains a\
                              dictionary \n named \'farm_dict\' that contains a description\
                              of the farm.',
                        required=True)
    parser.add_argument("-I", "--extra-includes", nargs='+',
                        help='Extra OKS includes for the output database.',
                        required=False, type=str, default=[])
    parser.add_argument("--dcm-only", required=False, default=False,
                        action="store_true",
                        help="Indicates whether a dcm-only \
                              configuration is needed.")
    parser.add_argument("--hltpu-only", required=False, default=False,
                        action="store_true",
                        help="Indicates whether a PU-only \
                              configuration is needed.")
    parser.add_argument("--local", required=False, default=False,
                        action="store_true",
                        help="Indicates whether a localhost \
                              configuration is needed.")
    parser.add_argument("-z", "--post-processor", required=False, default=None,
                        help="Point to a Python module containing a \
                              modify function that \n\ takes as input \
                              the database created by the script and\
                              modifies it in some way.Useful if\
                              creating a non-standard segment or\
                              partition.")

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



