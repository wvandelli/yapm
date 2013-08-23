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


sfos = [local_host]
hltsv_host = local_host
controller_host = local_host

farm_dict = partition(controller_host, dcm_segments, hltsv_host, sfos)
pprint(farm_dict)
