import pm.farm
import farm_utils
from pprint import pprint
import sys
from pm_test import *
from P1racks import P1racks
from operator import attrgetter
import socket
import string

host_name = string.split(socket.gethostname(), '.')[0]

dcm_segments = []
testbed_hosts = farm_utils.get_hosts(['daq/hw/hosts.data.xml'])
service_node = testbed_hosts[host_name]
worker_nodes = []
dcm_segments.append(dcm_segment("HLT-Segment-01", service_node, worker_nodes,
                                service_node, service_node))


hltsv_host = testbed_hosts[host_name]
controller_host = testbed_hosts[host_name]

partition_name = "azar_test"
farm_dict = partition(partition_name, controller_host, dcm_segments, hltsv_host)
pprint(farm_dict)
