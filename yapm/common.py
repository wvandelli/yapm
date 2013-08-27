"""
This module creates all the common DAL objects that are needed by more than one
segment or they are created only once but their container segments are created
multiple times(template/aggregator applications)
"""

from pm.dal import dal
from config.dal import module as dal_module
import os

DEFAULT_INCLUDES = ['/daq/hw/hosts.data.xml',
                    'daq/segments/setup.data.xml',
                    'daq/schema/hltsv.schema.xml',
                    'daq/schema/HLTMPPU.schema.xml',
                    'daq/sw/repository.data.xml',
                    'daq/schema/dcm.schema.xml',
                    'daq/sw/tags.data.xml',
                    'daq/sw/common-templates.data.xml'
                    ]

def create_config_rules(config_db):
    """
    Create the default publishing configuration and the efio
    configuration that are used by multiple segments/objects
    and add them to the database so they can be accessed when
    needed.
    """
    is_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')
    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    default_is_publishing = (is_dal.ISPublishingParameters
                             ("DefaulISpublishingParameters"))
    default_is_publishing.PublishInterval = 5
    default_is_publishing.ISServer = "${TDAQ_IS_SERVER=DF}"

    default_oh_publishing = (is_dal.OHPublishingParameters
                             ("DefaulOHpublishingParameters"))
    default_oh_publishing.PublishInterval = 5
    default_oh_publishing.OHServer = "${TDAQ_OH_SERVER=Histogramming}"
    default_oh_publishing.ROOTProvider = "${TDAQ_APPLICATION_NAME}"

    is_config_rule = is_dal.ConfigurationRule("DefaultISRule")
    is_config_rule.Parameters = default_is_publishing

    oh_config_rule = is_dal.ConfigurationRule("DefaultOHRule")
    oh_config_rule.Parameters = default_oh_publishing

    def_config_rules = (is_dal.ConfigurationRuleBundle
                        ("DefaultConfigurationRuleBundle"))
    def_config_rules.Rules.append(oh_config_rule)
    def_config_rules.Rules.append(is_config_rule)

    efio_config = dcm_dal.EFIOConfiguration("EFIO-Configuration-1")
    efio_config.MaxEFIOHandlers = 15
    efio_config.SFI_EFD_AckTimeout_ms = 5000
    efio_config.EFD_SFO_RcvTimeout_ms = 5000
    efio_config.HiddenParams.append("DelayConnect_s=2")
    efio_config.NetMask = "10.148.0.0/16"
    
    config_db.addObjects([def_config_rules, efio_config])

def create_pu_apps(config_db):
    """
    Create the HLTMPPU template and the HLTRC application and
    return a list containing them.
    """
    hltmppu_template = create_hltmppu_template(config_db)
    hltrc_app = create_hltrc_application(config_db)
    return [hltmppu_template, hltrc_app]
    
def create_hltmppu_template(config_db):
    """
    Create the HLTMPPU template application and return it.
    """
    hltpu_dal = dal_module("hltpu_dal", "daq/schema/HLTMPPU.schema.xml")
    app_parameters = "-n ${TDAQ_APPLICATION_NAME} -d libHLTMPPU.so"
    hltmppu_template = hltpu_dal.HLTMPPUApplication("HLTMPPU-Template")
    hltmppu_template.Parameters = app_parameters
    hltmppu_template.RestartParameters = app_parameters
    hltmppu_template.InitTimeout = 0
    hltmppu_main = config_db.getObject("Binary", "HLTMPPU_main")
    hltmppu_template.Program = hltmppu_main
    hltmppu_template.RestartableDuringRun = True

    return hltmppu_template

def create_template_applications(config_db, dcm_only, hltpu_only,
                                 sfos_exist):
    """
    Create the template applications for the HLT Segment(s) and return
    a list containing them to be used directly as input to the
    TemplateApplications relation of an HLT Segment.  The arguments
    serve as directives to know which applications to create and for
    their internal parameter tuning.

    Arguments:
      dcm_only -- indicates whether this is a DCM only
                  configuration (boolean)
      hltpu_only -- indicates whether this is
                    a PU only configuration (boolean)
      sfos_exist -- indicates whether there are SFOs
                    in the farm description (boolean)

    Returns:
      A list containing the template applications created based
      on the arguments given to the function.
    """
    if dcm_only:
        templ_apps = create_dcm_application(config_db, sfos_exist,
                                            dcm_only)
    elif hltpu_only:
        templ_apps = create_pu_apps(config_db)
    else:
        templ_apps = (create_dcm_application(config_db, sfos_exist,
                                             dcm_only) +
                      create_pu_apps(config_db))

    return templ_apps

def create_hltrc_application(config_db):
    """
    Create an HLTRC application.
    """
    config_rules = config_db.getObject("ConfigurationRuleBundle",
                                       "DefaultConfigurationRuleBundle")
    hltpu_dal = dal_module("hltpu_dal", "daq/schema/HLTMPPU.schema.xml")

    hlt_data_source = hltpu_dal.HLTDFDCMBackend("hltDataSource")
    hlt_data_source.library = "dfinterfaceDcm"

    hlt_mon_service = hltpu_dal.HLTMonInfoImpl("MonInfoService")

    hlt_mon_service.ConfigurationRules = config_rules

    #now time to create the actual HLTMPPU application
    hltrc_app = hltpu_dal.HLTRCApplication("HLTRC")
    hltrc_app.DataSource = hlt_data_source
    hltrc_app.InfoService = hlt_mon_service
    hltrc_bin = config_db.getObject("Binary", "HLTRC_main")
    hltrc_app.Program = hltrc_bin
    
    return hltrc_app

    
def create_dcm_application(config_db, sfos_exist, standalone):
    """
    Create a DCM application object using the arguments to
    tune its parameters and return a list containing the
    application.

    Arguments:
      sfos_exist -- indicates whether there are SFOs
                    in the farm description (boolean)
      standalone -- indicates whether this is a DCM only
                    configuration (boolean)
      
    """
    dcm_main = config_db.getObject("Binary", "dcm_main")

    config_rules = config_db.getObject("ConfigurationRuleBundle",
                                       "DefaultConfigurationRuleBundle")
    efio_config = config_db.getObject("EFIOConfiguration",
                                      "EFIO-Configuration-1")
    dcm_dal = dal_module("is_dal", 'daq/schema/dcm.schema.xml')

    #sources
    hltsv_l1source = dcm_dal.DcmHltsvL1Source("hltsv_l1source")
    dummy_source = dcm_dal.DcmDummyL1Source("DCMDummyL1Source-1")
    
    #data collectors
    dcm_ros_dc = dcm_dal.DcmRosDataCollector("dcm_ros_dc")
    dcm_ros_dc.nRequestCredits = 20
    dcm_dummy_dc = dcm_dal.DcmDummyDataCollector("DCMDummyDataCollector")
    
    #processor applications
    dcm_dummy_processor = dcm_dal.DcmDummyProcessor("dcm_dummy_processor")
    dcm_hltpu_processor = dcm_dal.DcmHltpuProcessor("dcm_hltpu_processor")

    #output applications
    dcm_file_output = dcm_dal.DcmFileOutput("dcm_file_output")
    dcm_file_output.storageAcceptance = 0
    dcm_efio_output = dcm_dal.DcmSfoEfioOutput("DcmSfoEfioOutput-1")
    dcm_efio_output.EfioConfiguration = efio_config
    dcm_sfo_output = dcm_dal.DcmSfoOutput("SFO-OutConfiguration-1")
    
    dcm_app = dcm_dal.DcmApplication("dcm")
    dcm_app.RestartableDuringRun = True
    dcm_app.l1Source = hltsv_l1source
    dcm_app.dataCollector = dcm_ros_dc
    if standalone:
        dcm_app.processor = dcm_dummy_processor
    else:
        dcm_app.processor = dcm_hltpu_processor
        
    if sfos_exist:
        dcm_app.output = dcm_efio_output
    else:
        dcm_app.output = dcm_file_output

    dcm_app.Program = dcm_main
    dcm_app.ConfigurationRules = config_rules

    return [dcm_app]

def create_aggregator_app(config_db, script_name, default_host,
                          segment_name=""):
    """
    Create an aggregator application, either a rack level one
    or a top-level one and return it.

    Arguments:
      script_name -- name of the aggregator script
      default_host -- where the aggregator app should run
      segment name -- name of segment where it runs(default "" for top level)
    """
    dal_script_name = os.path.splitext(script_name)[0]
##     aggregator_script = dal.Script(dal_script_name)
##     aggregator_script.BinaryName = script_name
##     repository = config_db.getObject("SW_Repository", "Online")
##     aggregator_script.BelongsTo = repository
##     config_db.updateObjects([aggregator_script])
    
    if not segment_name == "":
        aggregator_script = config_db.getObject("Script", "aggregator")
        aggregator_app = dal.Application("DCM-" + aggregator_script.id + "-" +
                                         segment_name)
    else:
        aggregator_script = config_db.getObject("Script", "top_aggregator")
        aggregator_app = dal.Application("DCM-" + aggregator_script.id)
    aggregator_app.Program = aggregator_script
    aggregator_app.RunsOn = default_host
    aggregator_app.Parameters = "-T DCM"
    aggregator_app.RestartParameters = "-T DCM"
    aggregator_app.InitTimeout = 0
    aggregator_app.RestartableDuringRun = True
    env_tdaq_python_home = config_db.getObject('Variable', 'TDAQ_PYTHON_HOME')
    env_pyhtonpath = config_db.getObject('Variable', 'PYTHONPATH')
    aggregator_app.ProcessEnvironment = [env_tdaq_python_home, env_pyhtonpath]

    return aggregator_app
