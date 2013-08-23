#! /usr/bin/env tdaq_python

"""
This module provides a few utility functions for geoname to coordinate conversions as well as the following objects:

idx2geo --> dictionary for index to geo conversion e.g. idx2geo['01'] = 'Y.13-06.D2'geo2idx --> dictionary for geo to index conversion e.g. geo2idx['Y.13-06.D2'] =  '01'
Rack --> class representing one rack
P1racks --> list of Rack objects: all the racks found in the OKS DB
"""


def geotorcl(geoname):
    """ Y.13-06.D2 --> (6,13,2) """

    rc,l =geoname.split('.')[1:]
    l = int(l[1:]) #'D2' --> 2
    c,r = map(int, rc.split('-')) #'13-06' --> 13,6
    return (r,c,l)
    
def rcltogeo(r,c,l):
    """ (6,13,2) --> Y.13-06.D2 """

    return 'Y.%02d-%02d.D%1d' % (c,r,l)


def _buildgeo2idx():

    idx2geo = {}
    
    for idx in xrange(1,96):

        l = r = c = 0

        if idx < 44:
            ##Level 2
            l = 2

            if idx > 8:
                ## Row 4 & 2
                r = 4
                c = 29 - idx
                if c < 3:
                    r = 2
                    c += 17 
            
            else:
                ## Row 6
                r = 6
                if idx <= 6:
                    c = 14 - idx
                else:
                    c = 11 - idx
                
        else:
            ##Level 1
            l = 1
            r = 6
            c = idx - 41

            if c > 19:
                r -= 2
                c -= 17
            if c > 20:
                r -= 2
                c-= 18

        idx2geo['%02d' % idx] = rcltogeo(r,c,l)

    return idx2geo


idx2geo = _buildgeo2idx()
geo2idx = dict([(v,k) for k,v in idx2geo.items()])
del k,v

class Rack(object):
    """
    Represents a rack. Includes the type (xpu,ef), the geoname and the index,
    and the list of LFS(s) and nodes. The latter are objects of type
    config.dal.Computer
    """
    
    def __init__(self, nodes = None, lfs = None, \
                 geoname = None, idx = None,  type='xpu'):

        if geoname and idx:
            raise ValueError("Either 'geoname' or 'idx' must be used, not both")

        if geoname:
            self.geoname = geoname
            self.idx = geo2idx[self.geoname]
        elif idx:
            self.idx = idx
            self.geoname = idx2geo[self.idx]
        else:
            raise ValueError("Either 'geoname' or 'idx' must be not None")
        
        self.nodes = nodes
        self.type = type
        self.lfsnodes = lfs

    def __str__(self):
        fmt = 'rack: %s idx: %s   lfs: %s  type: %s  nodes: %2d    first: %s   last: %s'
        s = fmt % (self.geoname, self.idx, self.lfsnodes[0].id, self.type, \
                   len(self.nodes), self.nodes[0].id, self.nodes[-1].id)
        return s

    def __repr__(self):
        return self.__str__()


def _fetchnodes(holder, input):

    for el in input:
        try:
            lst = el.Contains
            _fetchnodes(holder, lst)
        except AttributeError:
            holder.append(el)
        

def _fetchracks():
    import pm.project
    from operator import attrgetter
  
    db = pm.project.Project('daq/hw/hosts.data.xml')

    racks = db.getObject('Rack')

    result = []
    
    for r in racks:
        type = r.id.split('-',1)[0]
        idx = r.id.split('-',2)[-1]
        lfs = []
        _fetchnodes(lfs, r.LFS)
        nodes = []
        _fetchnodes(nodes, r.Nodes)
        nodes.sort(key=attrgetter('id'))
        result.append(Rack(nodes, lfs, idx = idx, type = type ))

    return result


P1racks = _fetchracks()


        
if __name__ == '__main__':

   for r in P1racks:
       print r

