
def modify(config_db):
    dcm_app = config_db.getObject("DcmApplication", "dcm")
    dcm_app.IfFailed = "Ignore"
    dcm_app.maxConnectDelay_s = 30
    dcm_app.sbaDirectory = "/local_L/dcmSba"
    dcm_app.hiddenParameters = ["disableRosAwareness"]
    dcm_app.maxConnectDelay_s = 0

    config_db.updateObjects([dcm_app])
    
    roib_input = config_db.getObject("RoIBPluginInternal", "plugin_internal")
    roib_input.IsMasterTrigger = True
    config_db.updateObjects([roib_input])

    try:
        hltrc_app = config_db.getObject("HLTRCApplication", "HLTRC")
        hltrc_app.numForks = 12
        hltrc_app.IfFailed = "Ignore"
        config_db.updateObjects([hltrc_app])
    except RuntimeError:
        pass

    try:
        hltmppu_app = config_db.getObject("HLTMPPUApplication", "HLTMPPU-Template")
        hltmppu_app.IfFailed = "Ignore"
    except RuntimeError:
        pass
