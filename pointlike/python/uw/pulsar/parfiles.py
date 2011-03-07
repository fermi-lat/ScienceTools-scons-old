import numpy as np

def sex2dec(s,mode='ra'):
    toks = s.split(':')
    multi = (-1 if '-' in s else 1) * (15 if mode == 'ra' else 1)
    return multi*sum( (60**(-i) * abs(float(toks[i])) for i in xrange(len(toks)) ) )

def ra2dec(s): return sex2dec(s,mode='ra')
def decl2dec(s): return sex2dec(s,mode='decl')

class ParFile(dict):

    def __init__(self,parfile):
        self.parfile = parfile
        for line in file(parfile):
            tok = line.strip().split()
            if len(tok)==0: continue
            self[tok[0]] = tok[1:] if (len(tok[1:]) > 1) else tok[1:][0]
    
    def get(self,key,first_elem=True,type=str):
        t = self[key]
        if first_elem and hasattr(t,'__iter__'):
            return type(t[0]) if first_elem else [type(x) for x in t] 
        return type(t)

    def get_ra(self): return ra2dec(self.get('RAJ'))
    
    def get_dec(self): return decl2dec(self.get('DECJ'))

    def get_skydir(self):
        from skymaps import SkyDir
        ra = ra2dec(self.get('RAJ'))
        dec = decl2dec(self.get('DECJ'))
        return SkyDir(ra,dec)

    def p(self,error=False):
        f0 = self.get('F0',first_elem=not error)
        if error and hasattr(f0,'__iter__'):
            f0,err = float(f0[0]),float(f0[-1])
            return 1./f0,err/f0**2
        return 1./float(f0)
 
    def pdot(self,error=False):
        f0 = self.get('F0',first_elem=not error)
        f1 = self.get('F1',first_elem=not error)
        if error and hasattr(f0,'__iter__'):
            f0,f0_err = float(f0[0]),float(f0[-1])
            f1,f1_err = float(f1[0]),float(f1[-1])
            pdot = -f1/f0**2
            pdot_err = 1./f0**2*(f1_err**2+4*pdot*f0_err**2)**0.5
            return pdot,pdot_err
        return -float(f1)/float(f0)**2

    def edot(self,mom=1e45):
        om = self.get('F0',type=float)*(np.pi*2)
        omdot = self.get('F1',type=float)*(np.pi*2)
        return -mom*om*omdot

    def has_waves(self):
        return np.any(['WAVE' in key for key in self.keys()])

    def is_msp(self,maxp=0.03,maxpdot=1e-18):
        return (self.p() < maxp) and (self.pdot() < maxpdot) and (not self.has_waves())

    def get_time_cuts(self):
        import datetime
        import time
        from uw.utilities.fermitime import utc_to_met
        tomorrow = datetime.date.fromtimestamp(time.time()+86400)
        tmin = 239557418 # first photon timestamp
        tmax = utc_to_met(tomorrow.year,tomorrow.month,tomorrow.day)
        if self.is_msp():
            return tmin,tmax
        t0 = self.get('START',type=float)
        t1 = self.get('FINISH',type=float)
        mjd_0 = 51910 + 7.428703703703703e-4
        met_0 = (t0 - mjd_0) * 86400
        met_1 = (t1 - mjd_0) * 86400
        return max(met_0,0), max(met_1,0)

class TimFile(object):

    def __init__(self,timfile):
        efac = 1
        toas = []
        for line in file(timfile):
            toks = line.strip().split()
            if toks[0] == 'EFAC':
                efac = float(toks[1])
                continue
            if line[0] == ' ':
                # is a TOA
                toa =   {
                        'TEL':str(toks[0]),
                        'FREQ':float(toks[1]),
                        'MJD':float(toks[2]),
                        'ERR':float(toks[3])*efac,
                        }
                toas += [toa] 
        self.toas = toas

    def get_mjds(self):
        return np.asarray([toa['MJD'] for toa in self.toas],dtype=float)

    def get_errs(self):
        return np.asarray([toa['ERR'] for toa in self.toas],dtype=float)
