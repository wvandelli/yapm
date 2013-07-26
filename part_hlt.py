from pm.project import Project
from pm.dal import dal, DFdal
from config.dal import module as dal_module
import sys
from farm_utils import *
import os
from pprint import pprint

def create_gatherer_application(db, segment_name):
     gatherer_app = DFdal.GATHERERApplication("Gatherer-" + segment_name)
     gatherer_app.Parameters = "-n Gatherer-" + segment_name
     gatherer_app.RestartParameters = "-n Gatherer-" + segment_name
     gatherer_app.Program = db.getObject("Binary", "Gatherer")
     gatherer_config = db.getObject("GATHERERConfiguration", "GathererConfiguration-Segment")
     gatherer_app.GATHERERConfiguration.append(gatherer_config)
     db.updateObjects([gatherer_app])

     return gatherer_app

def create_aggregator_app(db, script_name, default_host, segment_name):
     dal_script_name = os.path.splitext(script_name)[0]
     aggregator_script = dal.Script(dal_script_name)
     aggregator_script.BinaryName = script_name
     repository = db.getObject("SW_Repository", "Det TDAQ")
     aggregator_script.BelongsTo = repository
     db.updateObjects([aggregator_script])
     if not segment_name == "":
          aggregator_app = dal.Application("DCM-" + dal_script_name + "-" + segment_name)
     else:
          aggregator_app = dal.Application("DCM-" + dal_script_name)
     aggregator_app.Program = aggregator_script
     aggregator_app.RunsOn = default_host
     aggregator_app.Parameters = "5"
     aggregator_app.RestartParameters = "5"
     aggregator_app.InitTimeout = 0
     aggregator_app.RestartableDuringRun = True
     env_tdaq_python_home = db.getObject('Variable', 'TDAQ_PYTHON_HOME')
     env_pythonpath = db.getObject('Variable', 'PYTHONPATH')
     aggregator_app.ProcessEnvironment = [env_tdaq_python_home, env_pythonpath]
     db.updateObjects([aggregator_app])
     return aggregator_app

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
     hltrc_app = db.getObject("HLTMPPUApplication", "HLTRC")
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
     """
     aggregator_app = (create_aggregator_app(db, "aggregator.py",
                                             dcm_args['default_host'], name))
     dcm_segment.Applications.append(aggregator_app)
     """
          
     #infrastructure applications
     is_server = (create_is_server(db, "DF-" + name + "-iss", "TDAQ_IS_SERVER",
                                   dcm_args['is_resource']))
     oh_server = (create_is_server(db, "Histogramming-" + name + "-iss",
                                   "TDAQ_OH_SERVER",
                                   dcm_args['is_histogram']))
     db.updateObjects([is_server, oh_server])
     rdb = db.getObject("InfrastructureTemplateApplication", "DefNestedRDB")
     dcm_segment.Infrastructure = [is_server, oh_server, rdb]

     #Resources
     gatherer_app = create_gatherer_application(db, name)
     dcm_segment.Resources.append(gatherer_app)
     
     db.updateObjects([dcm_segment])
     return dcm_segment
