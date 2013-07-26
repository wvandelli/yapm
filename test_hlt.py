import pm.farm
from farm_utils import *
from pprint import pprint
import sys
from pm_test import *
from operator import attrgetter
import argparse
from pm.project import Project
from part_hlt import create_dcm_segment
import sys

def main():
    db = Project("azar_test.data.xml")
    farm_filename = sys.argv[1]
    print farm_filename
    exec("from " + farm_filename + " import farm_dict")
    dcm = farm_dict['dcms'][0]
    dcm_segment = create_dcm_segment(db=db,dcm_only = False, hltpu_only = True,**dcm)

    hlt_segment = db.getObject("Segment", "HLT")
    hlt_segment.Segments.append(dcm_segment)
    db.updateObjects([hlt_segment])
                        
if __name__ == "__main__":
    main()
