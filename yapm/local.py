import re
import logging
from pm.project import Project
from pm.dal import dal, DFdal
from config.dal import module as dal_module

def get_localinfo():
    """Runs through the known commands and fetch information for the local node.
 
     This method will fetch the information for the current node (CPU,
     architecture, network connectivity), without using SSH (which is faster).
     """
    import commands
    
    # The commands executed in each node.
    comm = [ 'hostname -f', 
             'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies',
             'cat /proc/cpuinfo', 
             'cat /proc/meminfo', 
             '/sbin/ifconfig', 
             'cat /etc/redhat-release', 
             'uname -m' ]
    
    retval = {'ssh': {'return': 0}, 'applications': {}}
    for c in comm:
        (status, output) = commands.getstatusoutput(c)
        retval['applications'][c] = {}
        retval['applications'][c]['status'] = status
        retval['applications'][c]['stdout'] = output

    return retval 

def decode_nodeinfo(info):
    """Decode the cpu, memory and net information returned by the OS. 

    Receives the cpuInfo, memInfo and netInfo strings, obtained by
    'cat/proc/cpuinfo', 'cat /proc/meminfo' and '/sbin/ifconfig', respectively.
    This method so, extracts the hardware information from these strings, and
    stores them in a map object.

    Keyword arguments (may be named):
    
    info -- The information returned by the FarmScanner.SSH_COMMAND.
    
    Returns a configured dal.Computer object with the retrieved information

    TODO: This needs a separated implementation for each decoder so it is simpler
    to read.
    """
    
    #Splitting the information.
    hostInfo = info['hostname -f']['stdout']
    cpufreq_safr = info['cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies']['stdout']
    cpuInfo = info['cat /proc/cpuinfo']['stdout']
    memInfo = info['cat /proc/meminfo']['stdout']
    netInfo = info['/sbin/ifconfig']['stdout']
    osInfo = info['cat /etc/redhat-release']['stdout']
    archInfo = info['uname -m']['stdout']
    
    #Adding the node name.
    ret = dal.Computer(re.search(r'\S+', hostInfo).group(0))
    ret.CPU = int(re.search(r'cpu MHz\s*:\s*(\d+)', cpuInfo).group(1))
    if len(cpufreq_safr) > 0: # then this should be a string with integer frequencies in kHz
        txt = cpufreq_safr.split()[0]
        try:
            ret.CPU = int(txt)/1000 # return MHz
        except ValueError:
            # this machine doesn't seem to support the
            # scaling_available_frequencies string
            # get speed from cpuinfo instead
            ret.CPU = None # dummy value while debugging
            ll = cpuInfo.split('\n')
            for l in ll:
                indx = l.find('cpu MHz')
                if indx >= 0:
                    ret.CPU = float(l.split(':')[1])
                    break
            if ret.CPU == None:
                ret.CPU = 1.0
                logging.warning("Could not determine CPU Frequency, set to 1.0 MHz")

    mem = int(float(re.search(r'MemTotal\s*:\s*(\d+)', memInfo).group(1)) / 1000.0)
    if ret.Memory > 65535:
        logging.warning("setting Memory to 65535 MB, since Computer@schema won't allow greater values")
    ret.Memory = min(mem,65535)
    ret.NumberOfCores = len(re.findall(r'processor\s*:\s*\d+', cpuInfo))
    ret.Type = re.search(r'model name\s*:\s*(.+)', cpuInfo).group(1)
    #Getting the hardware tag information.
    #Calculating the correct HW tag.
    #Getting the OS tag.
    osName = osInfo.strip()
    osVersion = 'slc5'
    if (re.search('release 6', osName) is not None): osVersion = 'slc6'
    
    #Checing whther it is a valid architecture.
    regExp = re.compile(r'(?P<ARCH>\S+)-\S+')
    value = '%s-%s' % (archInfo, osVersion)
    try: 
        ret.HW_Tag = value 
    except ValueError, e:
        logging.warning("Problems setting hardware tag to %s at %s, forcing to %s" % \
                (value, ret.fullName(), fallback_hwtag))

    #Getting the network info.
    netInterfacesList = re.split('\n\n', netInfo)
    regExp = re.compile(r'\s*(?P<LABEL>\S+).+HWaddr\s*(?P<MAC>\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)\s+.+inet addr:(?P<IP>\d+\.\d+\.\d+\.\d+)')
    ret.Interfaces = []
    for netInt in netInterfacesList:
        n = regExp.match(netInt)
        if n is not None:
            netInt = dal.NetworkInterface('%s-%s' %(ret.id, n.group('LABEL')))
            netInt.IPAddress = n.group('IP')
            #netInt.MACAddress = n.group('MAC')
            netInt.InterfaceName = n.group('LABEL')
            ret.Interfaces.append(netInt)

    return ret



def local_computer():
    """Returns a dal.Computer object for the current computer."""
    try:
        return decode_nodeinfo(get_localinfo()['applications'])
    except:
        import socket
        name = socket.gethostname()
        logging.warning("Problems decoding node info for (local) node %s" % name)
        return dal.Computer(name,State=False,HW_Tag=fallback_hwtag)
    return None
