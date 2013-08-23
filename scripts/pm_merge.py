"""
This module takes as arguments a config db file describing a plain partition and 
a config db containing an hltsv segment and merges them together
"""

from pm.project import Project
import argparse
import string

def merge(args):
    partition_name = string.split(args.partition_file, ".")[0]
    part_db = Project(args.partition_file)
    part_db.addInclude(args.segment_file)
    part_db.commit()
    partition = part_db.getObject("Partition", partition_name)
    hltsv_segment = part_db.getObject("Segment", "HLT")
    partition.Segments.append(hltsv_segment)
    part_db.updateObjects([partition])

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--partition-file",
                        required=True, type=str)

    parser.add_argument("-s", "--segment-file",
                        required=True, type=str)

    return parser

def command_line_runner():
    parser = get_parser()
    args = parser.parse_args()

    merge(args)

if __name__ == "__main__":
    command_line_runner()
