"""
This module creates the DAL component representation of the HLTSV segment
and all other DAL components which are specific to this segment.
"""

from pm.dal import dal, DFdal
from config.dal import module as dal_module
from common import create_aggregator_app

def create_sfo_application(config_db, number, host):
    """
    Create an SFO application and return it.

    Arguments:
      config_db -- the database under creation
      
      number -- a unique number identifier for the application
      
      host -- a DAL computer object where the application should run

    """
    efio_config = config_db.getObject("EFIOConfiguration", "EFIO-Configuration-1")
    #first create the app configuration
    sfo_config = DFdal.SFOConfiguration("SFO-Configuration-" + number)
    sfo_config.BufferSize_kB = 10240
    sfo_config.DataRecordingEnabled = False
    sfo_config.LumiBlockEnabled = False
    sfo_config.DirectoriesToWriteData.append("/tmp")
    sfo_config.DirectoryWritingTime = 60
    sfo_config.DirectoryChangeTime = 15
    sfo_config.DirectoryToWriteIndex = "/tmp"
    sfo_config.EFIOConfiguration = efio_config

    #now create the application itself
    sfo_app = DFdal.SFOApplication("SFO-"+number)
    sfo_app.ActionTimeout = 30
    sfo_app.IfError = "Restart"
    sfo_app.RestartableDuringRun = True
    sfo_app.IfDies = "Restart"
    sfo_app.RunsOn = host
    sfo_binary = config_db.getObject("Binary", "SFOng_main")
    sfo_app.Program = sfo_binary
    sfo_app.SFOConfiguration = sfo_config

    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    dc_is_resource = dcm_dal.DC_ISResourceUpdate("DCAppConf-" + number +
                                                 "-ISResourceUpdate-SFO")
    dc_is_resource.name = "SFO"
    dc_is_resource.delay = 10
    dc_is_resource.activeOnNodes.append("SFO")

    dc_app_config = dcm_dal.DCApplicationConfig("DCAppConfig-"+number)
    dc_app_config.ISDefaultRsrcUpdateInterval = 5
    dc_app_config.ISDefaultServer = "*DF"
    dc_app_config.refDC_ISResourceUpdate.append(dc_is_resource)

    sfo_app.DFApplicationConfig = dc_app_config
    
    return sfo_app

def create_hltsv_app(config_db, hltsv_host):
    """
    Create an HLTSV application and return it.

    Arguments:
      config_db -- the configuration database
      
      hltsv_host -- a DAL computer object where the application should run
      
    """
    config_rules = config_db.getObject("ConfigurationRuleBundle",
                                       "DefaultConfigurationRuleBundle")
    hltsv_dal = dal_module("hltsv_dal", 'daq/schema/hltsv.schema.xml')
    
    roib_plugin = hltsv_dal.RoIBPluginInternal("plugin_internal")
    roib_plugin.Libraries.append("libsvl1internal")

    hltsv_main = config_db.getObject("Binary", "hltsv_main")
    
    hltsv_app = hltsv_dal.HLTSVApplication("HLTSV")
    hltsv_app.ConfigurationRules = config_rules
    hltsv_app.RoIBInput = roib_plugin
    hltsv_app.Program = hltsv_main
    hltsv_app.RunsOn = hltsv_host
    
    return hltsv_app

def create_hltsv_segment(config_db, default_host, hltsv_host, sfos, hlt_segments):
    """
    Create a top-level HLT segment and return it.

    Arguments:
      config_db -- configuration database
      
      default_host -- a DAL Computer object serving as the
                      main host for the segment
                      
      hltsv_host -- a DAL Computer object to run the HLTSV application

      sfos -- a list of DAL Computer objects to run the SFO applications

      hlt_segments -- a list of HLT segments to add to this top-level
                      segment. HLT Segment as returned by:
                      yapm.hlt.create_hlt_segment
                      
    """
    config_rules = config_db.getObject("ConfigurationRuleBundle",
                                       "DefaultConfigurationRuleBundle")
    efio_config = config_db.getObject("EFIOConfiguration", "EFIO-Configuration-1")
    hltsv_segment = dal.Segment("HLT")
    defrc_controller = config_db.getObject("RunControlTemplateApplication",
                                           "DefRC")
    hltsv_segment.IsControlledBy = defrc_controller
    hltsv_app = create_hltsv_app(config_db, hltsv_host)

    sfo_apps = []
    for index, sfo_host in zip(range(1, len(sfos)+1), sfos):
        sfo_application = create_sfo_application(config_db, str(index),
                                                 sfo_host)
        sfo_apps.append(sfo_application)
        
    hltsv_resources = [hltsv_app] + sfo_apps
    hltsv_segment.Resources = hltsv_resources

    top_aggregator_app = create_aggregator_app(config_db, "top_aggregator.py",
                                               default_host)
    hltsv_segment.Applications = [top_aggregator_app]

    hltsv_segment.DefaultHost = default_host

    #infrastructure applications
    is_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_IS")
    oh_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_Histogramming")
    hltsv_segment.Infrastructure = [is_server, oh_server]
    
    #Resources
    mon_is = config_db.getObject("MIGApplication", "TopMIG-IS")
    mon_oh = config_db.getObject("MIGApplication", "TopMIG-OH")
    hltsv_segment.Resources.append(mon_is)
    hltsv_segment.Resources.append(mon_oh)

    hltsv_segment.Segments = hlt_segments
        
    return hltsv_segment
