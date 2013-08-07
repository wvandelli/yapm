import pm.farm
import farm_utils
from pprint import pprint
import sys
from pm_test import *
from P1racks import P1racks
from operator import attrgetter



#create 2 dcm segments
testbed_hosts = farm_utils.get_hosts(['daq/hw/hosts.data.xml'])
dcm1_hosts = pm.farm.subselect_pattern(testbed_hosts,
                                       'pc-tbed-r3-[%02d-%02d]' % (1,10))
dcm2_hosts = pm.farm.subselect_pattern(testbed_hosts,
                                       'pc-tbed-r3-[%02d-%02d]' % (11,20))

dcm_racks = [sorted(dcm1_hosts.values()), sorted(dcm2_hosts.values())]
dcm_segments = []
for idx, rack in enumerate(dcm_racks):
    worker_nodes = rack[0:-1]
    service_node = rack[-1]
    dcm_segments.append(dcm_segment("HLT-Segment-%02d" % idx, service_node,
                                    worker_nodes, service_node, service_node))

hltsv_host = testbed_hosts['pc-tbed-r3-01']
controller_host = testbed_hosts['pc-tbed-r3-02']

sfos = pm.farm.subselect_pattern(testbed_hosts,
                                 'pc-tbed-r3-[%02d-%02d]' % (21,22))
partition_name = "azar_test"
farm_dict = partition(partition_name, controller_host, dcm_segments,
                      hltsv_host, sfos.values())
pprint(farm_dict)

