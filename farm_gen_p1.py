"""
This module is used to create a farm dictionary object for P1
used by the partition-maker script
"""
import pm
import farm_utils
from pprint import pprint
from P1racks import P1racks
from operator import attrgetter
import sys


P1racks.sort(key=attrgetter('idx'))

accepted = []

for i in range(65, 70):
    accepted.append("%02d" % i)
        
dcm_segments = []
for rack in P1racks:
    worker_nodes = rack.nodes[0:-1]
    service_node = rack.nodes[-1]
    dcm_segments.append(farm_utils.dcm_segment("HLT-Segment-" + rack.idx,
                                               service_node, worker_nodes,
                                               service_node, service_node))

hosts = farm_utils.get_hosts(['daq/hw/hosts.data.xml'])
hltsv_host = hosts['pc-tdq-dc-02']
controller_host = hosts['pc-tdq-onl-80']

sfos = [hosts['pc-tdq-sfo-%02d' % n] for n in range(1,13)]
farm_dict = farm_utils.partition(controller_host, dcm_segments,
                                 hltsv_host, sfos)

pprint(farm_dict)
