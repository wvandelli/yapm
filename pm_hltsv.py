"""
This module creates the DAL component representation of the HLTSV segment
and all other DAL components which are speficic to this segment.
"""

from pm.dal import dal, DFdal
from config.dal import module as dal_module
from pm_common import create_aggregator_app

def create_top_gatherer(db):
    gatherer_dal = dal_module("gatherer_dal",
                              'daq/schema/MonInfoGatherer.schema.xml')
    gatherer_algorithm = db.getObject("MIGAlgorithm",
                                      "DefaultGathererAlgorithm")
    info_handler = db.getObject("MIGInformationHandler",
                                "DefaultGathererInformationHandler")
    gatherer_config_top = (gatherer_dal.
                           MIGConfiguration("GathererConfiguration-Top"))
    gatherer_config_top.ProviderRegExp = "Histogramming-.*"
    top_histo_server = db.getObject("InfrastructureApplication",
                                    "Histogramming")
    gatherer_config_top.SourceServers = [top_histo_server]
    gatherer_config_top.DestinationServers = [top_histo_server]
    gatherer_config_top.InformationHandler = info_handler
    gatherer_config_top.Algorithm = gatherer_algorithm
    db.updateObjects([gatherer_config_top])

    top_gatherer_app = gatherer_dal.MIGApplication("Gatherer-Top")
    gatherer_bin = db.getObject("Binary", "MonInfoGatherer")
    top_gatherer_app.Program = gatherer_bin
    top_gatherer_app.Configurations = [gatherer_config_top]
    db.updateObjects([top_gatherer_app])
    return top_gatherer_app

def create_sfo_application(db, number, host):
    """
    Creates an SFO application with a specific id(number argument) to be used
    in its name. So for example an SFO taking as argument number 1 will be named
    SFO-01 etc. The host is the machine that the SFO application will run on.
    """
    #first create the app configuration
    sfo_config = DFdal.SFOConfiguration("SFO-Configuration-" + number)
    sfo_config.BufferSize_kB = 10240
    sfo_config.DataRecordingEnabled = False
    sfo_config.LumiBlockEnabled = False
    sfo_config.DirectoriesToWriteData.append("/tmp")
    sfo_config.DirectoryWritingTime = 60
    sfo_config.DirectoryChangeTime = 15
    sfo_config.DirectoryToWriteIndex = "/tmp"
    efio_config = db.getObject("EFIOConfiguration", "EFIO-Configuration-1")
    sfo_config.EFIOConfiguration = efio_config
    db.updateObjects([sfo_config])

    #now create the application itself
    sfo_app = DFdal.SFOApplication("SFO-"+number)
    sfo_app.ActionTimeout = 30
    sfo_app.IfError = "Restart"
    sfo_app.RestartableDuringRun = True
    sfo_app.IfDies = "Restart"
    sfo_app.RunsOn = host
    sfo_binary = db.getObject("Binary", "SFOng_main")
    sfo_app.Program = sfo_binary
    sfo_app.SFOConfiguration = sfo_config

    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    dc_is_resource = dcm_dal.DC_ISResourceUpdate("DCAppConf-" + number +
                                "-ISResourceUpdate-SFO")
    dc_is_resource.name = "SFO"
    dc_is_resource.delay = 10
    dc_is_resource.activeOnNodes.append("SFO")
    db.updateObjects([dc_is_resource])

    dc_app_config = dcm_dal.DCApplicationConfig("DCAppConfig-"+number)
    dc_app_config.ISDefaultRsrcUpdateInterval = 5
    dc_app_config.ISDefaultServer = "*DF"
    dc_app_config.refDC_ISResourceUpdate.append(dc_is_resource)
    db.updateObjects([dc_app_config])

    sfo_app.DFApplicationConfig = dc_app_config
    
    db.updateObjects([sfo_app])
    return sfo_app

def create_hltsv_app(db, hltsv_host):
    hltsv_dal = dal_module("hltsv_dal", 'daq/schema/hltsv.schema.xml')
    is_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    
    def_config_rules = db.getObject("ConfigurationRuleBundle",
                         "DefaultConfigurationRuleBundle")
    
    roib_plugin = hltsv_dal.RoIBPluginInternal("plugin_internal")
    roib_plugin.Libraries.append("libsvl1internal")
    db.updateObjects([roib_plugin])

    hltsv_main = db.getObject("Binary", "hltsv_main")
    
    hltsv_app = hltsv_dal.HLTSVApplication("HLTSV")
    hltsv_app.ConfigurationRules = def_config_rules
    hltsv_app.RoIBInput = roib_plugin
    hltsv_app.Program = hltsv_main
    hltsv_app.RunsOn = hltsv_host
    db.updateObjects([hltsv_app])
    
    return hltsv_app

def create_hlt_segment(db, default_host, hltsv_host, sfos):
    top_gatherer_app = create_top_gatherer(db)
    
    hltsv_segment = dal.Segment("HLT")
    defrc_controller = db.getObject("RunControlTemplateApplication", "DefRC")
    hltsv_segment.IsControlledBy = defrc_controller
    hltsv_app = create_hltsv_app(db, hltsv_host)

    sfo_apps = []
    for index, sfo_host in enumerate(sfos):
        sfo_application = create_sfo_application(db, str(index), sfo_host)
        sfo_apps.append(sfo_application)
        
    hltsv_resources = [hltsv_app, top_gatherer_app] + sfo_apps
    hltsv_segment.Resources = hltsv_resources
    
    hltsv_segment.DefaultHost = default_host

    aggregator_app = create_aggregator_app(db, "top_aggregator.py",
                             default_host)
    hltsv_segment.Applications.append(aggregator_app)

    db.updateObjects([hltsv_segment])
    
    return hltsv_segment

def add_dcm_segments(db, dcm_segments):
    hltsv_segment = db.getObject("Segment", "HLT")
    #add all the dcm segments to the hlt segment
    for d_segment in dcm_segments:
        hltsv_segment.Segments.append(d_segment)
       
    db.updateObjects([hltsv_segment])