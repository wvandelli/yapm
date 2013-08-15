"""
This module creates all the common DAL objects that are needed by more than one
segments or they are created only once but their container segments are created
multiple times(template applications)
"""

from pm.dal import dal
from config.dal import module as dal_module
import os


DEFAULT_INCLUDES = ['daq/segments/setup.data.xml',
                    'daq/schema/hltsv.schema.xml',
                    'daq/sw/repository.data.xml',
                    'dcm/schema/dcm_is.schema.xml',
                    'daq/schema/HLTMPPU.schema.xml',
                    'daq/schema/MonInfoGatherer.schema.xml',
                    'daq/schema/dcm.schema.xml',
                    'daq/sw/tags.data.xml',
                    'daq/segments/ROS/ROS-LAR-emulated-dc.data.xml',
                    'daq/sw/common-templates.data.xml'
                    ]

def create_default_gatherer_options(config_db):
    gatherer_dal = dal_module("gatherer_dal",
                              'daq/schema/MonInfoGatherer.schema.xml')
    gatherer_algorithm = gatherer_dal.MIGAlgorithm("DefaultGathererAlgorithm")
    config_db.updateObjects([gatherer_algorithm])
    info_handler = (gatherer_dal.
                    MIGInformationHandler("DefaultGathererInformationHandler"))
    info_handler.Algorithm = gatherer_algorithm
    config_db.updateObjects([info_handler])

def create_config_rules(config_db):
    is_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    default_is_publishing = (is_dal.ISPublishingParameters
                             ("DefaulISpublishingParameters"))
    default_is_publishing.PublishInterval = 5
    default_is_publishing.ISServer = "${TDAQ_IS_SERVER=DF}"
    config_db.updateObjects([default_is_publishing])

    default_oh_publishing = (is_dal.OHPublishingParameters
                             ("DefaulOHpublishingParameters"))
    default_oh_publishing.PublishInterval = 5
    default_oh_publishing.OHServer = "${TDAQ_OH_SERVER=Histogramming}"
    default_oh_publishing.ROOTProvider = "${TDAQ_APPLICATION_NAME}"
    config_db.updateObjects([default_oh_publishing])

    is_config_rule = is_dal.ConfigurationRule("DefaultISRule")
    is_config_rule.Parameters = default_is_publishing
    config_db.updateObjects([is_config_rule])

    oh_config_rule = is_dal.ConfigurationRule("DefaultOHRule")
    oh_config_rule.Parameters = default_oh_publishing
    config_db.updateObjects([oh_config_rule])

    def_config_rules = (is_dal.ConfigurationRuleBundle
                        ("DefaultConfigurationRuleBundle"))
    def_config_rules.Rules.append(oh_config_rule)
    def_config_rules.Rules.append(is_config_rule)
    config_db.updateObjects([def_config_rules])

def create_hltpu_templates(config_db):
    """
    Here create the template applications of the DCM segments
    that only need to be created once
    """
    #first create the hltmppu template
    app_parameters = "-n ${TDAQ_APPLICATION_NAME} -d libHLTMPPU.so"
    hltmppu_template = dal.TemplateApplication("HLTMPPU-Template")
    hltmppu_template.Parameters = app_parameters
    hltmppu_template.RestartParameters = app_parameters
    hltmppu_template.InitTimeout = 0
    hltmppu_main = config_db.getObject("Binary", "HLTMPPU_main")
    hltmppu_template.Program = hltmppu_main
    hltmppu_template.RestartableDuringRun = True
    config_db.updateObjects([hltmppu_template])

    create_hltpu_application(config_db)

def create_template_applications(config_db, dcm_only,
                                 hltpu_only, sfos_exist):
    if dcm_only:
        create_dcm_application(config_db, sfos_exist, standalone=True)
    elif hltpu_only:
        create_hltpu_templates(config_db)
    else:
        create_dcm_application(config_db, sfos_exist, standalone=False)
        create_hltpu_templates(config_db)

def create_hltpu_application(config_db):
    hltpu_dal = dal_module("hltpu_dal", "daq/schema/HLTMPPU.schema.xml")

    hlt_data_source = hltpu_dal.HLTDFDCMBackend("hltDataSource")
    config_db.updateObjects([hlt_data_source])

    hlt_mon_service = hltpu_dal.HLTMonInfoImpl("MonInfoService")
    def_con_rules = config_db.getObject("ConfigurationRuleBundle" , 
                                        "DefaultConfigurationRuleBundle")
    hlt_mon_service.ConfigurationRules = def_con_rules
    config_db.updateObjects([hlt_mon_service])

    #now time to create the actual HLTMPPU application
    hltrc_app = hltpu_dal.HLTRCApplication("HLTRC")
    hltrc_app.DataSource = hlt_data_source
    hltrc_app.InfoService = hlt_mon_service
    hltrc_bin = config_db.getObject("Binary", "HLTRC_main")
    hltrc_app.Program = hltrc_bin
    config_db.updateObjects([hltrc_app])
    return hltrc_app

    
def create_dcm_application(config_db, sfos_exist, standalone):
    config_rules = (config_db.getObject("ConfigurationRuleBundle",
                                 "DefaultConfigurationRuleBundle"))
    dcm_main = config_db.getObject("Binary", "dcm_main")
    
    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    #sources
    hltsv_l1source = dcm_dal.DcmHltsvL1Source("hltsv_l1source")
    dummy_source = dcm_dal.DcmDummyL1Source("DCMDummyL1Source-1")
    config_db.updateObjects([hltsv_l1source, dummy_source])
    
    #data collectors
    dcm_ros_dc = dcm_dal.DcmRosDataCollector("dcm_ros_dc")
    dcm_dummy_dc = dcm_dal.DcmDummyDataCollector("DCMDummyDataCollector")
    config_db.updateObjects([dcm_ros_dc, dcm_dummy_dc])
    
    #processor applications
    dcm_dummy_processor = dcm_dal.DcmDummyProcessor("dcm_dummy_processor")
    dcm_hltpu_processor = dcm_dal.DcmHltpuProcessor("dcm_hltpu_processor")
    config_db.updateObjects([dcm_dummy_processor, dcm_hltpu_processor])

    #output applications
    dcm_file_output = dcm_dal.DcmFileOutput("dcm_file_output")
    dcm_file_output.storageAcceptance = 0
    config_db.updateObjects([dcm_file_output])
    efio_config = dcm_dal.EFIOConfiguration("EFIO-Configuration-1")
    efio_config.MaxEFIOHandlers = 15
    efio_config.HiddenParams.append("DelayConnect_s=2")
    efio_config.SFI_EFD_AckTimeout_ms = 600000
    efio_config.EFD_SFO_RcvTimeout_ms = 600000
    efio_config.NetMask = "10.148.0.0/16"
    config_db.updateObjects([efio_config])
    dcm_efio_output = dcm_dal.DcmSfoEfioOutput("DcmSfoEfioOutput-1")
    dcm_efio_output.EfioConfiguration = efio_config
    config_db.updateObjects([dcm_efio_output])
    dcm_sfo_output = dcm_dal.DcmSfoOutput("SFO-OutConfiguration-1")
    config_db.updateObjects([dcm_sfo_output])
    
    dcm_app = dcm_dal.DcmApplication("dcm")
    dcm_app.l1Source = hltsv_l1source
    dcm_app.dataCollector = dcm_dummy_dc
    if standalone:
        dcm_app.processor = dcm_dummy_processor
    else:
        dcm_app.processor = dcm_hltpu_processor
        
    if sfos_exist:
        dcm_app.output = dcm_sfo_output
    else:
        dcm_app.output = dcm_file_output

    dcm_app.Program = dcm_main
    dcm_app.ConfigurationRules = config_rules

    config_db.updateObjects([dcm_app])
    return dcm_app

def create_aggregator_app(config_db, script_name, default_host,
                          segment_name=""):
    dal_script_name = os.path.splitext(script_name)[0]
    aggregator_script = dal.Script(dal_script_name)
    aggregator_script.BinaryName = script_name
    repository = config_db.getObject("SW_Repository", "Online")
    aggregator_script.BelongsTo = repository
    config_db.updateObjects([aggregator_script])
    if not segment_name == "":
        aggregator_app = dal.Application("DCM-" + dal_script_name + "-" +
                                         segment_name)
    else:
        aggregator_app = dal.Application("DCM-" + dal_script_name)
    aggregator_app.Program = aggregator_script
    aggregator_app.RunsOn = default_host
    aggregator_app.Parameters = "-T DCM"
    aggregator_app.RestartParameters = "-T DCM"
    aggregator_app.InitTimeout = 0
    aggregator_app.RestartableDuringRun = True
    env_tdaq_python_home = config_db.getObject('Variable', 'TDAQ_PYTHON_HOME')
    env_pyhtonpath = config_db.getObject('Variable', 'PYTHONPATH')
    aggregator_app.ProcessEnvironment = [env_tdaq_python_home, env_pyhtonpath]
    config_db.updateObjects([aggregator_app])
    return aggregator_app
