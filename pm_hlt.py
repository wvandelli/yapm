"""
This module creates a dal representation object for an HLT segment
and all directly related objects(gatherer, IS servers)
"""

from pm.dal import dal
from config.dal import module as dal_module
from pm_common import create_aggregator_app

def create_gatherer_application(db, segment_name, segment_oh_server):
    app_name = "Gatherer-" + segment_name
    gatherer_dal = dal_module("gatherer_dal",
                              'daq/schema/MonInfoGatherer.schema.xml')
    gatherer_algorithm = db.getObject("MIGAlgorithm",
                                      "DefaultGathererAlgorithm")
    info_handler = db.getObject("MIGInformationHandler",
                                "DefaultGathererInformationHandler")

    gatherer_config_segment = (gatherer_dal.MIGConfiguration
                               ("GathererConfiguration-" + segment_name))
    gatherer_config_segment.SourceServers = [segment_oh_server]
    top_histo_server = db.getObject("InfrastructureApplication",
                                    "Histogramming")
    gatherer_config_segment.DestinationServers = [top_histo_server]
    gatherer_config_segment.InformationHandler = info_handler
    gatherer_config_segment.Algorithm = gatherer_algorithm
    db.updateObjects([gatherer_config_segment])

    segment_gatherer_app = gatherer_dal.MIGApplication(app_name)
    gatherer_bin = db.getObject("Binary", "MonInfoGatherer")
    segment_gatherer_app.Program = gatherer_bin
    segment_gatherer_app.Configurations = [gatherer_config_segment]
    db.updateObjects([segment_gatherer_app])

    return segment_gatherer_app

def create_is_server(db, server_name, env_var, host):
    is_server = dal.InfrastructureApplication(server_name)
    is_server_binary = db.getObject("Binary", "is_server")
    is_server.Program = is_server_binary
    is_server.Parameters = "-s -p ${TDAQ_PARTITION} -n" + server_name
    is_server.RestartParameters = "-s -p ${TDAQ_PARTITION} -n" + server_name
    is_server.SegmentProcEnvVarName = env_var
    is_server.IfDies = "Restart"
    is_server.IfFailed = "Restart"
    is_server.RestartableDuringRun = True
    is_server.RunsOn = host
    return is_server

def create_dcm_only(db):
    dcm_app = db.getObject("DcmApplication", "dcm")
    return [dcm_app]

def create_hltpu_only(db):
    hltrc_app = db.getObject("HLTRCApplication", "HLTRC")
    hltmppu_template = db.getObject("TemplateApplication", "HLTMPPU-Template")
    return [hltrc_app, hltmppu_template]

def create_both(db):
    return create_dcm_only(db) + create_hltpu_only(db)

def create_dcm_segment(**dcm_args):
    db = dcm_args['db']
    name = dcm_args['name']

    dcm_segment = dal.HLTSegment(name)
    if dcm_args['hltpu_only'] and not dcm_args['dcm_only']:
        dcm_segment.TemplateApplications = create_hltpu_only(db)
    elif (dcm_args['dcm_only'] and not dcm_args['hltpu_only']):
        dcm_segment.TemplateApplications = create_dcm_only(db)
    else:
        dcm_segment.TemplateApplications = create_both(db)

    #add hosts to segment
    for machine in dcm_args['hosts']:
        dcm_segment.TemplateHosts.append(machine)

    dcm_segment.DefaultHost = dcm_args['default_host']

    defrc_controller = db.getObject("RunControlTemplateApplication", "DefRC")
    dcm_segment.IsControlledBy = defrc_controller

    aggregator_app = (create_aggregator_app(db, "aggregator.py",
                                            dcm_args['default_host'], name))
    dcm_segment.Applications.append(aggregator_app)

    #infrastructure applications
    rdb = db.getObject("InfrastructureTemplateApplication", "DefRDB")
    is_server = db.getObject("InfrastructureTemplateApplication", "DF_IS")
    oh_server = db.getObject("InfrastructureTemplateApplication",
                             "DF_Histogramming")

    dcm_segment.Infrastructure = [is_server, oh_server, rdb]

    #Resources
    """
    gatherer_app = create_gatherer_application(db, name, oh_server)
    dcm_segment.Resources.append(gatherer_app)
    """
    db.updateObjects([dcm_segment])
    return dcm_segment
