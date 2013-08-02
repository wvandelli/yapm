#!/usr/bin/env tdaq_python

from pm.project import Project
from pm.dal import dal, DFdal
from config.dal import module as dal_module
import sys
from farm_utils import *
import os

includes = ['daq/segments/setup.data.xml',
            'daq/schema/hltsv.schema.xml',
            'daq/schema/HLTMPPU.schema.xml',
            'daq/sw/repository.data.xml',
            'dcm/schema/dcm_is.schema.xml',
            'daq/schema/dcm.schema.xml',
            'daq/sw/tags.data.xml',
            'daq/segments/ROS/ROS-LAR-emulated-dc.data.xml']
tags = [
       'x86_64-slc6-gcc47-opt',
       'x86_64-slc6-gcc47-dbg'
       'x86_64-slc5-gcc47-opt',
       'x86_64-slc5-gcc47-dbg',
      ]

def create_config_rules(db):
    is_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    
    default_is_publishing = is_dal.ISPublishingParameters("DefaulISpublishingParameters")
    default_is_publishing.PublishInterval = 5
    default_is_publishing.ISServer = "${TDAQ_IS_SERVER=DF}"
    db.updateObjects([default_is_publishing])
    
    default_oh_publishing = is_dal.OHPublishingParameters("DefaulOHpublishingParameters")
    default_oh_publishing.PublishInterval = 5
    default_oh_publishing.OHServer = "${TDAQ_OH_SERVER=Histogramming}"
    default_oh_publishing.ROOTProvider = "${TDAQ_APPLICATION_NAME}"
    db.updateObjects([default_oh_publishing])

    is_config_rule = is_dal.ConfigurationRule("DefaultISRule")
    is_config_rule.Parameters = default_is_publishing
    db.updateObjects([is_config_rule])

    oh_config_rule = is_dal.ConfigurationRule("DefaultOHRule")
    oh_config_rule.Parameters = default_oh_publishing
    db.updateObjects([oh_config_rule])
    
    def_config_rules = is_dal.ConfigurationRuleBundle("DefaultConfigurationRuleBundle")
    def_config_rules.Rules.append(oh_config_rule)
    def_config_rules.Rules.append(is_config_rule)
    db.updateObjects([def_config_rules])

def create_template_applications(db):
    """
    Here create the template applications of the DCM segments that only need to be created once
    """
    #first create the hltmppu template
    hltmppu_template = dal.TemplateApplication("HLTMPPU-Template")
    hltmppu_template.Parameters = "-n ${TDAQ_APPLICATION_NAME} -d libHLTMPPU.so"
    hltmppu_template.RestartParameters = "-n ${TDAQ_APPLICATION_NAME} -d libHLTMPPU.so"
    hltmppu_template.InitTimeout = 0
    hltmppu_main = db.getObject("Binary", "HLTMPPU_main")
    hltmppu_template.Program = hltmppu_main
    hltmppu_template.RestartableDuringRun = True
    db.updateObjects([hltmppu_template])
    create_hltpu_application(db)
    create_dcm_application(db)

def create_hltsv_app(db, hltsv_host):
    hltsv_dal = dal_module("hltsv_dal", 'daq/schema/hltsv.schema.xml')
    is_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    def_config_rules = db.getObject("ConfigurationRuleBundle", "DefaultConfigurationRuleBundle")
    
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

def create_hltpu_application(db):
    hltpu_dal = dal_module("hltpu_dal", "daq/schema/HLTMPPU.schema.xml")
    
    hlt_data_source = hltpu_dal.HLTDataSourceImpl("hltDataSource")
    hlt_data_source.library = "DFDummyBackend"
    db.updateObjects([hlt_data_source])
    
    hlt_mon_service = hltpu_dal.HLTInfoServiceImpl("MonSvcInfoService")
    hlt_mon_service.library = "MonSvcInfoService"
    db.updateObjects([hlt_mon_service])

    #now time to create the actual HLTMPPU application
    hltrc_app = hltpu_dal.HLTMPPUApplication("HLTRC")
    hltrc_app.DataSource = hlt_data_source
    hltrc_app.InfoService = hlt_mon_service
    hltrc_bin = db.getObject("Binary", "HLTRC_main")
    hltrc_app.Program = hltrc_bin
    db.updateObjects([hltrc_app])
    return hltrc_app

    
def create_dcm_application(db):
    config_rules = (db.getObject("ConfigurationRuleBundle",
                            "DefaultConfigurationRuleBundle"))
    dcm_main = db.getObject("Binary", "dcm_main")
    
    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    #sources
    hltsv_l1source = dcm_dal.DcmHltsvL1Source("hltsv_l1source")
    dummy_source = dcm_dal.DcmDummyL1Source("DCMDummyL1Source-1")
    db.updateObjects([hltsv_l1source, dummy_source])
    
    #data collectors
    dcm_ros_dc = dcm_dal.DcmRosDataCollector("dcm_ros_dc")
    dcm_dummy_dc = dcm_dal.DcmDummyDataCollector("DCMDummyDataCollector")
    db.updateObjects([dcm_ros_dc, dcm_dummy_dc])
    
    #processor applications
    dcm_dummy_processor = dcm_dal.DcmDummyProcessor("dcm_dummy_processor")
    db.updateObjects([dcm_dummy_processor])

    #output applications
    dcm_file_output = dcm_dal.DcmFileOutput("dcm_file_output")
    dcm_file_output.storageAcceptance = 0
    db.updateObjects([dcm_file_output])
    efio_config = dcm_dal.EFIOConfiguration("EFIO-Configuration-1")
    efio_config.MaxEFIOHandlers = 15
    efio_config.HiddenParams.append("DelayConnect_s=2")
    efio_config.SFI_EFD_AckTimeout_ms = 600000
    efio_config.EFD_SFO_RcvTimeout_ms = 600000
    efio_config.NetMask = "10.148.0.0/16"
    db.updateObjects([efio_config])
    dcm_efio_output = dcm_dal.DcmSfoEfioOutput("DcmSfoEfioOutput-1")
    dcm_efio_output.EfioConfiguration = efio_config
    db.updateObjects([dcm_efio_output])
    
    dcm_app = dcm_dal.DcmApplication("dcm")
    dcm_app.l1Source = hltsv_l1source
    dcm_app.dataCollector = dcm_ros_dc
    dcm_app.processor = dcm_dummy_processor
    dcm_app.output = dcm_file_output
    dcm_app.Program = dcm_main
    dcm_app.ConfigurationRules = config_rules

    db.updateObjects([dcm_app])
    return dcm_app

def create_infrastructure_app(db, name, env_var, host):
    is_server = dal.InfrastructureApplication(name)
    is_server_binary = db.getObject("Binary", "is_server")
    is_server.Program = is_server_binary
    is_server.Parameters = "-s -p ${TDAQ_PARTITION} -n" + name
    is_server.RestartParameters = "-s -p ${TDAQ_PARTITION} -n" + name
    is_server.SegmentProcEnvVarName = env_var
    is_server.IfDies = "Restart"
    is_server.IfFailed = "Restart"
    is_server.RestartableDuringRun = True
    is_server.RunsOn = host
    return is_server

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
    repository = db.getObject("SW_Repository", "Online")
    aggregator_script.BelongsTo = repository
    db.updateObjects([aggregator_script])
    if not segment_name == "":
        aggregator_app = dal.Application("DCM-" + dal_script_name + "-" + segment_name)
    else:
        aggregator_app = dal.Application("DCM-" + dal_script_name)
    aggregator_app.Program = aggregator_script
    aggregator_app.RunsOn = default_host
    aggregator_app.Parameters = "-T DCM"
    aggregator_app.RestartParameters = "-T DCM"
    aggregator_app.InitTimeout = 0
    aggregator_app.StartAt = "SOR"
    aggregator_app.RestartableDuringRun = True
    env_tdaq_python_home = db.getObject('Variable', 'TDAQ_PYTHON_HOME')
    env_pyhtonpath = db.getObject('Variable', 'PYTHONPATH')
    aggregator_app.ProcessEnvironment = [env_tdaq_python_home, env_pyhtonpath]
    db.updateObjects([aggregator_app])
    return aggregator_app

def create_hlt_segment(db, default_host, hltsv_host, dcm_segments):
    gatherer_storage_segment = DFdal.HistogramStorage("GathererStorage-Segment")
    gatherer_storage_segment.ISServerName = "${TDAQ_OH_SERVER}"
    db.updateObjects([gatherer_storage_segment])

    gatherer_storage_top = DFdal.HistogramStorage("GathererStorage-Top")
    gatherer_storage_top.ISServerName = "Histogramming"
    db.updateObjects([gatherer_storage_top])

    gatherer_receiver_segment = DFdal.HistogramReceiverConfig("GathererReceiver-Segment")
    gatherer_receiver_segment.Storage.append(gatherer_storage_segment)
    db.updateObjects([gatherer_receiver_segment])

    gatherer_provider_segment = DFdal.HistogramProviderConfig("GathererProvider-Segment")
    gatherer_provider_segment.Storage.append(gatherer_storage_top)
    gatherer_provider_segment.PublishProviderName = "${TDAQ_OH_SERVER}"
    gatherer_provider_segment.UseHistory = False
    gatherer_provider_segment.UpdateFrequency = 30
    gatherer_provider_segment.SummingMode = "Merge"
    gatherer_provider_segment.ResultContent = "Sum"
    db.updateObjects([gatherer_provider_segment])

    gatherer_receiver_top = DFdal.HistogramReceiverConfig("GathererReceiver-Top")
    gatherer_receiver_top.Storage.append(gatherer_storage_top)
    gatherer_receiver_top.Providers = "Histogramming-.*"
    db.updateObjects([gatherer_receiver_top])

    gatherer_provider_top = DFdal.HistogramProviderConfig("GathererProvider-Top")
    gatherer_provider_top.Storage.append(gatherer_storage_top)
    gatherer_provider_top.PublishProviderName = "Histogramming"
    gatherer_provider_top.UseHistory = False
    gatherer_provider_top.UpdateFrequency = 30
    gatherer_provider_top.SummingMode = "Merge"
    gatherer_provider_top.ResultContent = "Sum"
    db.updateObjects([gatherer_provider_top])

    gatherer_config_segment = DFdal.GATHERERConfiguration("GathererConfiguration-Segment")
    gatherer_config_segment.Input = gatherer_receiver_segment
    gatherer_config_segment.Output = gatherer_provider_segment
    db.updateObjects([gatherer_config_segment])

    gatherer_config_top = DFdal.GATHERERConfiguration("GathererConfiguration-Top")
    gatherer_config_top.Input = gatherer_receiver_top
    gatherer_config_top.Output = gatherer_provider_top
    db.updateObjects([gatherer_config_top])

    gatherer_app_top = DFdal.GATHERERApplication("Gatherer-Top")
    gatherer_app_top.Parameters = "-n Gatherer-Top"
    gatherer_app_top.RestartParameters = "-n Gatherer-Top"
    gatherer_app_top.Program = db.getObject("Binary", "Gatherer")
    gatherer_app_top.GATHERERConfiguration.append(gatherer_config_top)
    db.updateObjects([gatherer_app_top])
    
    hltsv_segment = dal.Segment("HLT")
    defrc_controller = db.getObject("RunControlTemplateApplication", "DefRC")
    hltsv_segment.IsControlledBy = defrc_controller
    hltsv_app = create_hltsv_app(db, hltsv_host)

    sfo_app_1 = create_sfo_application(db, "1", "pc-tbed-r3-21.cern.ch")
    sfo_app_2 = create_sfo_application(db, "2", "pc-tbed-r3-22.cern.ch")
    sfo_app_3 = create_sfo_application(db, "3", "pc-tbed-r3-23.cern.ch")
    sfo_app_4 = create_sfo_application(db, "4", "pc-tbed-r3-24.cern.ch")
    
    hltsv_segment.Resources.append(hltsv_app)
    """
    hltsv_segment.Resources.append(sfo_app_1)
    hltsv_segment.Resources.append(sfo_app_2)
    hltsv_segment.Resources.append(sfo_app_3)
    hltsv_segment.Resources.append(sfo_app_4)
    """

    hltsv_segment.Resources.append(gatherer_app_top)
    hltsv_segment.DefaultHost = default_host

    aggregator_app = create_aggregator_app(db, "top_aggregator.py", default_host, "")
    hltsv_segment.Applications.append(aggregator_app)

    db.updateObjects([hltsv_segment])
    
    return hltsv_segment

def add_dcm_segments(db, dcm_segments):
    hltsv_segment = db.getObject("Segment", "HLT")
    #add all the dcm segments to the hlt segment
    for d_segment in dcm_segments:
        hltsv_segment.Segments.append(d_segment)
        
    db.updateObjects([hltsv_segment])
    
def create_sfo_application(db, number, host):
    #first create the app configuration
    sfo_config = DFdal.SFOConfiguration("SFO-Configuration-" + number)
    sfo_config.BufferSize_kB = 10240
    sfo_config.DataRecordingEnabled = False
    sfo_config.LumiBlockEnabled = False
    sfo_config.DirectoriesToWriteData.append("/raid_cntl1/data")
    sfo_config.DirectoryWritingTime = 60
    sfo_config.DirectoryChangeTime = 15
    sfo_config.DirectoryToWriteIndex = "/raid_cntl1/data"
    efio_config = db.getObject("EFIOConfiguration", "EFIO-Configuration-1")
    sfo_config.EFIOConfiguration = efio_config
    db.updateObjects([sfo_config])

    #now create the application itself
    sfo_app = DFdal.SFOApplication("SFO-"+number)
    sfo_app.ActionTimeout = 30
    sfo_app.IfError = "Restart"
    sfo_app.RestartableDuringRun = True
    sfo_app.IfDies = "Restart"
    sfo_app.RunsOn = db.getObject("Computer", host)
    sfo_binary = db.getObject("Binary", "SFO_main")
    sfo_app.Program = sfo_binary
    sfo_app.SFOConfiguration = sfo_config

    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    dc_is_resource = dcm_dal.DC_ISResourceUpdate("DCAppConf-"+number + "-ISResourceUpdate-SFO")
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

def create_counters(db):
    l1_rates = dal.IS_EventsAndRates("L1_counters")
    l1_rates.EventCounter = "DF.HLTSV.Events.LVL1Events"
    l1_rates.Rate = "DF.HLTSV.Events.Rate"
    db.updateObjects([l1_rates])
    l2_rates = dal.IS_EventsAndRates("L2_counters")
    l2_rates.EventCounter = "DF.DCM_summary_DF_top_sum.ProxL1Events" 
    l2_rates.Rate = "DF.DCM_summary_DF_top_sum.L1Rate"
    db.updateObjects([l2_rates])
    eb_rates = dal.IS_EventsAndRates("DF.DCM_summary_DF_top_sum.EB_counters")
    eb_rates.Rate = "DF.DCM_summary_DF_top_sum.EbRate"
    eb_rates.EventCounter = "DF.DCM_summary_DF_top_sum.EbEvents"
    db.updateObjects([eb_rates])
    ef_rates = dal.IS_EventsAndRates("DF.DCM_summary_DF_top_sum.EF_counters")
    ef_rates.Rate = "DF.DCM_summary_DF_top_sum.OutRate"
    ef_rates.EventCounter = ""
    db.updateObjects([ef_rates])
    
    daq_counters = dal.IS_InformationSources("DAQ_Counters")
    daq_counters.LVL1 = l1_rates
    daq_counters.LVL2 = l2_rates
    daq_counters.EB = eb_rates
    daq_counters.EF = ef_rates
    db.updateObjects([daq_counters])
    return daq_counters

def create_ros_segment(db):
     ros_segment = dal.Segment("ROS")

     for ros_unit in db.getObject("ROS"):
          ros_segment.Resources.append(ros_unit)

     defrc_controller = db.getObject("RunControlTemplateApplication", "DefRC")
     ros_segment.IsControlledBy = defrc_controller
     db.updateObjects([ros_segment])
     return ros_segment    
"""
def create_ros_segment(db):
    #get ros segment from included schema file
    ros_segment = db.getObject("Segment", "ROS-TDQ-emulated-dc")
    return ros_segment
"""
