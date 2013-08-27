"""
This module creates a dal representation object for an HLT segment
and all directly related objects
"""

from pm.dal import dal
from config.dal import module as dal_module
from common import create_aggregator_app

def create_hlt_segment(**dcm_args):
    """
    Create an HLT segment and return it.

    Keyword arguments:
      name -- name of the segment
      default_host -- a DAL Computer object serving as the
                      main host for the segment
      hosts -- worker hosts(DAL Computer objects) where the apps should run
      is_resource -- where the IS info from segment apps
                     are published(DAL Computer object)
      is_histogram -- where the histogram from segment apps
                      are published(DAL Computer object)
      config_db -- the configuration database
      templ_apps -- the template application to run on the worker nodes
                    of the segment as returned by:
                    yapm.common.create_template_applications
    """
    config_db = dcm_args['config_db']
    name = dcm_args['name']

    defrc_controller = config_db.getObject("RunControlTemplateApplication",
                                           "DefRC")
    aggregator_app = (create_aggregator_app(config_db, "aggregator.py",
                                            dcm_args['default_host'], name))

    #infrastructure applications
    rconfig_db = config_db.getObject("InfrastructureTemplateApplication",
                                     "DefRDB")
    is_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_IS")
    oh_server = config_db.getObject("InfrastructureTemplateApplication",
                                    "DF_Histogramming")

    #Resources
    mon_is = config_db.getObject("MIGApplication", "DefMIG-IS")
    mon_oh = config_db.getObject("MIGApplication", "DefMIG-OH")

    hlt_segment = dal.HLTSegment(id                   = name,
                                 TemplateApplications = dcm_args['templ_apps'],
                                 Resources            = [mon_is, mon_oh],
                                 Infrastructure       = [is_server, oh_server, rconfig_db],
                                 Applications         = [aggregator_app],
                                 IsControlledBy       = defrc_controller,
                                 DefaultHost          = dcm_args['default_host'],
                                 TemplateHosts        = dcm_args['hosts'])
    return hlt_segment
