import pm.farm

def get_hosts(host_files):
    """Returns a dictionary of Computer objects from the
    list of files that are passed as arguments
    """
    hosts = {}
    for include in host_files:
        hosts.update(pm.farm.load(include, short_names=True))
        
    return hosts

def hlt_segment(name, default_host, hosts, is_resource, is_histogram):
    """returns a dictionary representation of an HLT segment as expected by
    the partition making script
    """
    hlt_dict = {}
    hlt_dict['name'] = name
    hlt_dict['default_host'] = default_host
    hlt_dict['hosts'] = hosts
    hlt_dict['is_resource'] = is_resource
    hlt_dict['is_histogram'] = is_histogram
    return hlt_dict

def partition(default_host, hlts, hltsv, sfos):
    """returns a dictionary representation of a partition as expected by
    the partition making script
    """
    farm_dict = {}
    farm_dict['default_host'] = default_host
    farm_dict['hlts'] = hlts
    farm_dict['hltsv'] = hltsv
    farm_dict['sfos'] = sfos

    return farm_dict
    
