"""
This module creates a dal representation object for an HLT segment
and all directly related objects(gatherer, IS servers)
"""

from pm.dal import dal
from config.dal import module as dal_module
from pm_common import create_aggregator_app

def create_dcm_only(config_db):
    dcm_app = config_db.getObject("DcmApplication", "dcm")
    return [dcm_app]

def create_hltpu_only(config_db):
    hltrc_app = config_db.getObject("HLTRCApplication", "HLTRC")
    hltmppu_template = config_db.getObject("TemplateApplication",
                                           "HLTMPPU-Template")
    return [hltrc_app, hltmppu_template]

def create_both(config_db):
    return create_dcm_only(config_db) + create_hltpu_only(config_db)

def create_dcm_segment(**dcm_args):
    config_db = dcm_args['config_db']
    name = dcm_args['name']

    dcm_segment = dal.HLTSegment(name)
    if dcm_args['hltpu_only'] and not dcm_args['dcm_only']:
        dcm_segment.TemplateApplications = create_hltpu_only(config_db)
    elif (dcm_args['dcm_only'] and not dcm_args['hltpu_only']):
        dcm_segment.TemplateApplications = create_dcm_only(config_db)
    else:
        dcm_segment.TemplateApplications = create_both(config_db)

    #add hosts to segment
    for machine in dcm_args['hosts']:
        dcm_segment.TemplateHosts.append(machine)

    dcm_segment.DefaultHost = dcm_args['default_host']

    defrc_controller = config_db.getObject("RunControlTemplateApplication",
                                           "DefRC")
    dcm_segment.IsControlledBy = defrc_controller

    aggregator_app = (create_aggregator_app(config_db, "aggregator.py",
                                            dcm_args['default_host'], name))
    dcm_segment.Applications.append(aggregator_app)

    #infrastructure applications
    rconfig_db = config_db.getObject("InfrastructureTemplateApplication",
                                     "DefRDB")
    is_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_IS")
    oh_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_Histogramming")

    dcm_segment.Infrastructure = [is_server, oh_server, rconfig_db]

    #Resources
    mon_is = config_db.getObject("MIGApplication", "DefMIG-IS")
    mon_oh = config_db.getObject("MIGApplication", "DefMIG-OH")
    dcm_segment.Resources = [mon_is, mon_oh]

    config_db.updateObjects([dcm_segment])
    return dcm_segment
