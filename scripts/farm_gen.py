"""
This module is used to create a farm dictionary object used
by the partition-maker script
"""
import pm
from farm_utils import dcm_segment, partition, get_hosts
from pprint import pprint

#create 2 dcm segments
testbed_hosts = get_hosts(['daq/hw/hosts.data.xml'])
hlt1_hosts = pm.farm.subselect_pattern(testbed_hosts,
                                       'pc-tbed-r3-[%02d-%02d]' % (1,10))
hlt2_hosts = pm.farm.subselect_pattern(testbed_hosts,
                                       'pc-tbed-r3-[%02d-%02d]' % (11,20))

hlt_racks = [sorted(hlt1_hosts.values()), sorted(hlt2_hosts.values())]
hlt_segments = []
for idx, rack in zip(range(1, len(hlt_racks)+1), hlt_racks):
    worker_nodes = rack[0:-1]
    service_node = rack[-1]
    hlt_segments.append(hlt_segment("HLT-Segment-%02d" % idx, service_node,
                                    worker_nodes, service_node, service_node))

hltsv_host = testbed_hosts['pc-tbed-r3-01']
controller_host = testbed_hosts['pc-tbed-r3-02']

sfos = pm.farm.subselect_pattern(testbed_hosts,
                                 'pc-tbed-r3-[%02d-%02d]' % (21,22))

farm_dict = partition(controller_host, dcm_segments,
                      hltsv_host, sfos.values())
pprint(farm_dict)

