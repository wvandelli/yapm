"""
This module creates the DAL representation of a ROS segment and all related DAL
components. For now the configurable creation of a ROS segment is not supported
but rather it is imported from external files.
"""

from pm.dal import dal

def create_ros_segment(config_db):
    ros_segment = dal.Segment("ROS")

    for ros_unit in config_db.getObject("ROS"):
        ros_segment.Resources.append(ros_unit)

    defrc_controller = config_db.getObject("RunControlTemplateApplication",
                                           "DefRC")
    ros_segment.IsControlleconfig_dby = defrc_controller
    config_db.updateObjects([ros_segment])
    return ros_segment



#def create_ros_segment(config_db):
    #get ros segment from included schema file
#    ros_segment = config_db.getObject("Segment", "ROS-TDQ-emulated-dc")
#    return ros_segment
#
