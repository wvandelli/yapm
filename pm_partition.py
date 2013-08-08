"""
This module creates a dal object representation of a partition and directly
related objects(counters etc.)

"""
from pm.dal import dal, DFdal
from pm.project import Project

TAGS = [
        'x86_64-slc6-gcc47-opt',
        'x86_64-slc6-gcc47-dbg',
        'x86_64-slc5-gcc47-opt',
        'x86_64-slc5-gcc47-dbg',
       ]

def create_counters(db):
    l1_rates = dal.IS_EventsAndRates("L1_counters")
    l1_rates.EventCounter = "DF.HLTSV.Events.LVL1Events"
    l1_rates.Rate = "DF.HLTSV.Events.Rate"
    db.updateObjects([l1_rates])
    l2_rates = dal.IS_EventsAndRates("L2_counters")
    l2_rates.EventCounter = "DF.DCM-top_aggregator.DCM.top.sum.ProxL1Events"
    l2_rates.Rate = "DF.DCM_summary_DF_top_sum.L1Rate"
    db.updateObjects([l2_rates])
    eb_rates = (dal.IS_EventsAndRates
                ("DF.DCM-top_aggregator.DCM.top.sum.EB_counters"))
    eb_rates.Rate = "DF.DCM-top_aggregator.DCM.top.sum.EbRate"
    eb_rates.EventCounter = "DF.DCM-top_aggregator.DCM.top.sum.EbEvents"
    db.updateObjects([eb_rates])
    ef_rates = (dal.IS_EventsAndRates
                ("DF.DCM-top_aggregator.DCM.top.sum.EF_counters"))
    ef_rates.Rate = "DF.DCM-top_aggregator.DCM.top.sum.OutRate"
    ef_rates.EventCounter = ""
    db.updateObjects([ef_rates])

    daq_counters = dal.IS_InformationSources("DAQ_Counters")
    daq_counters.LVL1 = l1_rates
    daq_counters.LVL2 = l2_rates
    daq_counters.EB = eb_rates
    daq_counters.EF = ef_rates
    db.updateObjects([daq_counters])
    return daq_counters

def create_partition(**part_args):
    db = part_args['db']
    partition = dal.Partition(part_args['part_name'])

    partition.RepositoryRoot = part_args['repository_root']

    partition.Segments = part_args['segments']
    partition.OnlineInfrastructure = db.getObject("OnlineSegment", "setup")
    partition.LogRoot = '/logs/${TDAQ_VERSION}'
    partition.WorkingDirectory = '/logs'
    partition.RepositoryRoot = part_args['repository_root']

    #DF parameters
    df_parameters = DFdal.DFParameters("DataFlow")

    df_parameters.MulticastAddress = part_args['multicast_address']
    df_parameters.DefaultDataNetworks = part_args['data_networks']
    db.updateObjects([df_parameters])
    partition.DataFlowParameters = df_parameters

    common_params = db.getObject("VariableSet", "CommonParameters")
    partition.Parameters.append(common_params)
    external_params = db.getObject("VariableSet", "External-parameters")
    partition.Parameters.append(external_params)

    common_env = db.getObject("VariableSet", "CommonEnvironment")
    partition.ProcessEnvironment.append(common_env)

    for tag_name in TAGS:
        tag = db.getObject("Tag", tag_name)
        partition.DefaultTags.append(tag)

    partition.DefaultHost = part_args['default_host']

    daq_counters = create_counters(db)
    partition.IS_InformationSource = daq_counters
    
    pu_db = Project("PuDummy.data.xml")
    trig_config = pu_db.getObject("TriggerConfiguration", "TrigConf-1")
    partition.TriggerConfiguration = trig_config
    
    partition.Disabled.append(db.getObject("Segment", "ROS"))
    db.updateObjects([partition])
    return partition
