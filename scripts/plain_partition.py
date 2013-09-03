from pm.project import Project
import argparse
import yapm.partition
import imp

DEFAULT_INCLUDES = ['daq/segments/setup.data.xml']

def get_farm_dict(module_name):
    farm_gen = imp.find_module(module_name)
    farm_gen_mod = imp.load_module(module_name, farm_gen[0], farm_gen[1],
                                   farm_gen[2])

    return farm_gen_mod.farm_dict

def create_config_db(args):
    farm_dict = get_farm_dict(args.farm_file)
    full_includes = DEFAULT_INCLUDES + args.extra_includes
    config_db = Project("data/"+args.partition_name + ".data.xml", full_includes)


    part_params = {
                   'config_db'         : config_db,
                   'part_name'         : args.partition_name,
                   'repository_root'   : args.repository_root,
                   'segments'          : [],
                   'data_networks'     : args.data_networks,
                   'multicast_address' : args.multicast_address,
                   'default_host'      : farm_dict['default_host']
                   }

    yapm.partition.create_partition(**part_params)



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
    parser.add_argument("--local", required=False, default=False,
                        action="store_true")
    parser.add_argument("-p", "--partition-name", required=False,
                        default="az_test")
    return parser

def command_line_runner():
    parser = get_parser()
    args = parser.parse_args()


    create_config_db(args)

if __name__ == '__main__':
    command_line_runner()
