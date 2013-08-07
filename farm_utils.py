import pm.farm

def get_hosts(host_files):
    """Returns a dictionary of Computer objects from the
    list of files that are passed as arguments
    """
    hosts = {}
    for include in host_files:
        hosts.update(pm.farm.load(include, short_names=True))
        
    return hosts

def dcm_segment(name, default_host, hosts, is_resource, is_histogram):
    """returns a dictionary representation of a dcm segment as expected by
    the partition making script
    """
    dcm_dict = {}
    dcm_dict['name'] = name
    dcm_dict['default_host'] = default_host
    dcm_dict['hosts'] = hosts
    dcm_dict['is_resource'] = is_resource
    dcm_dict['is_histogram'] = is_histogram
    return dcm_dict

def partition(name, default_host, dcms, hltsv, sfos):
    """returns a dictionary representation of a dcm segment as expected by
    the partition making script
    """
    farm_dict = {}
    farm_dict['default_host'] = default_host
    farm_dict['dcms'] = dcms
    farm_dict['hltsv'] = hltsv
    farm_dict['sfos'] = sfos

    return farm_dict
    
