import pm.farm
import farm_utils
from pprint import pprint
import sys
from pm_test import *
from operator import attrgetter
import socket
import string
import local

local_host = local.local_computer()

dcm_segments = []
service_node = local_host
worker_nodes = [local_host]
dcm_segments.append(dcm_segment("HLT-Segment-01", service_node, worker_nodes,
                                service_node, service_node))

dcm_segments.append(dcm_segment("HLT-Segment-02", service_node, worker_nodes,
                                service_node, service_node))


hltsv_host = local_host
controller_host = local_host

partition_name = "azar_test"
farm_dict = partition(partition_name, controller_host, dcm_segments, hltsv_host)
pprint(farm_dict)
