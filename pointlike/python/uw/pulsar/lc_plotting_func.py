'''
Python module to plot phaseograms in different energy bands
Author(s): Damien Parent <dmnparent@gmail.com>, JCT
'''

__version__ = 1.9

import os, sys
from os.path import join, isfile
import numpy as np, pyfits
from numpy import array, vectorize, sqrt, exp, log10, power
from itertools import izip
from ROOT import *

from uw.utilities.coords import sepangle_deg
import uw.utilities.fits_utils as utilfits
import uw.utilities.root_utils as root
from uw.utilities.phasetools import weighted_h_statistic, h_statistic, z2m
from uw.pulsar.stats import sf_hm as h_sig, hm, hmw, sigma_trials, sig2sigma

# ===========================
# print in colors
# ===========================
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
OKRED = '\033[31m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'


def get_theta(par,energy):
    '''Get theta cut = (ROI x (e/100)**(alpha))**2 + beta**2'''
    if np.isscalar(energy):
        return sqrt(par[0]**2 * power(100./energy,par[1]*2.) + par[2]**2)
    else:
        return np.sqrt(par[0]**2 * np.power(100./energy,par[1]*2.) + par[2]**2)

def get_searchpulsation_weights(energy,angsep,theta,logeref,logesig):
    '''Calculate the weight of a given event based on Philippe s tool (i.e. SearchPulsation)'''
    if np.isscalar(energy):
        return exp(-(log10(energy)-logeref)**2/(2*logesig**2))*(1+angsep**2/(4./9.*theta**2))**-2.
    th2=theta*theta
    an2=angsep*angsep
    return np.exp(-np.power(np.log10(energy)-logeref,2.)/(2*logesig**2))*np.power(1+an2/(4./9.*th2),-2.)

def met2mjd(met):
    MJDREF = 51910. + 7.428703703703703E-4
    return met/86400. + MJDREF

def SetHistoBox(histo,xmin,xmax,color=18):
    xmin_histo = int(histo.GetXaxis().GetBinLowEdge(1))
    xmax_histo = int(histo.GetXaxis().GetBinUpEdge(histo.GetNbinsX()))   
    ymin, ymax = histo.GetMinimum(), histo.GetMaximum()
    boxes = []
    for i in range(xmax_histo-xmin_histo):
        if xmin<xmax:
            box = TBox(xmin+i,ymin,xmax+i,ymax); box.SetFillColor(color)
            boxes += [box]
        else:
            box1 = TBox(xmin+i,ymin,1+i,ymax); box1.SetFillColor(color)
            box2 = TBox(-1e-3+i,ymin,xmax+i,ymax); box2.SetFillColor(color)
            boxes += [box1,box2]
    return boxes

def SetHistoLine(histo,ymin,ymax,color=1):
    xmin = int(histo.GetXaxis().GetBinLowEdge(1))
    xmax = int(histo.GetXaxis().GetBinUpEdge(histo.GetNbinsX()))
    line = TLine(xmin,ymin,xmax,ymax)
    line.SetLineStyle(2); line.SetLineColor(color)
    return line

class PulsarLightCurve:
    '''Constructor of PulsarLightCurve'''
    def init(self):
        self.psrname        = ''
        self.ra_src         = None
        self.dec_src        = None
        self.radius         = None
        self.emin           = None
        self.emax           = None
        self.tmin           = None
        self.tmax           = None
        self.eclsmin        = 0
        self.eclsmax        = 1e9
        self.zenithcut      = 100.
        self.phase_colname  = 'PULSE_PHASE'
        self.weight_colname = 'WEIGHT'
        self.psfcut         = False
        self.convtype       = -2

    def __init__(self, ft1name, **kwargs):
        '''
        ============   =============================================
        keyword        description
        ============   =============================================
        ft1name        FT1 filename                      (necessary)
        ra_src         Right Ascension (deg)             [FT1 header]
        dec_src        Declination (deg)                 [FT1 header]
        psrname        source name                       ["PSR"]
        radius         Maximum radius (deg)              [FT1 header]
        emin           Minimum energy (MeV)              [FT1 header]
        emax           Maximum energy (MeV)              [FT1 header]
        tmin           Start time (MET)                  [FT1 header]
        tmax           End time (MET)                    [FT1 header]
        eclsmin        Minimum event class               [0]
        eclsmax        Maximum event class               [1e9]
        zenithcut      Zenith Cut (deg)                  [100.]
        phase_colname  Phase column name                 ["PULSE_PHASE"]
        weight_colname Weight column name                ["WEIGHT"]
        psfcut         PSF-cut selection [True/False]    [False]
        convtype       -1=both,0=both,-1=back (P6v3Diff) [-2]
                       -2=both (P7Source_V6)
        '''
        self.init()
        self.__dict__.update(kwargs)
        
        self.ft1name = ft1name
        if not isfile(ft1name):
            raise IOError("Cannot access to the ft1file. Exiting ...")
       
        #print "================="
        #print "  ", OKBLUE + self.psrname + ENDC
        #print "================="

        # time range
        ft1range = utilfits.ft1_time_range(ft1name)
        self.tmin = ft1range['START'] if self.tmin is None else self.tmin
        self.tmax = ft1range['STOP'] if self.tmax is None else self.tmax

        # energy range
        self.__energy_range  = [ [100.,3e5] , [3000.,3e5], [1000.,3e3], [300.,1000.], [100.,300.], [20., 100.], [3e3,3e5] ]
        self.emin = utilfits.get_header_erange(ft1name)[0] if self.emin is None else self.emin
        self.emax = utilfits.get_header_erange(ft1name)[1] if self.emax is None else self.emax

        for E in self.__energy_range:
            if E[0] < self.emin: E[0] = self.emin
            if E[1] > self.emax: E[1] = self.emax
            if E[0] > E[1]: E[1] = E[0]

        # position of the source (ra,dec)
        self.ra_src = utilfits.get_header_position(ft1name)[0] if self.ra_src is None else self.ra_src
        self.dec_src = utilfits.get_header_position(ft1name)[1] if self.dec_src is None else self.dec_src

        # radius selection
        self.radius = utilfits.get_header_position(ft1name)[2] if self.radius is None else self.radius
        self.__radius_range = []
        
        # psf selection
        self.__psf_selection = [5.12,0.8,0.07]
        if self.convtype == -1: self.__psf_selection = [5.12,0.8,0.07]
        elif self.convtype ==  0: self.__psf_selection = [3.3,0.8,0.05]
        elif self.convtype ==  1: self.__psf_selection = [5.5,0.8,0.1]
        elif self.convtype == -2: self.__psf_selection = [5.3,0.745,0.09]
        else: print "The selected convtype does not exist. Use the default convtype -1."

        # weight information
        self.weight = False

        # declaration of histograms (ROOT ...)
        self.nhisto       = len(self.__energy_range)
        self.nbins        = 32
        self.phase_shift  = 0
        self.phaseogram   = []
        self.phaseogram2D = []
        for i in range(self.nhisto):
            self.phaseogram.append(TH1F())
            self.phaseogram2D.append(TH2F())
            self.__radius_range += [self.radius]

        # ======================= EVENT FILE ============================
        #                Get the events from the FT1 file
        # ===============================================================
        ft1file = pyfits.open(ft1name)
        hduname = 'EVENTS'        
        ra = ft1file[hduname].data.field('RA')
        dec = ft1file[hduname].data.field('DEC')
        time = ft1file[hduname].data.field('TIME')
        energy = ft1file[hduname].data.field('ENERGY')
        evtclass = ft1file[hduname].data.field('EVENT_CLASS')
        zenith_angle = ft1file[hduname].data.field('ZENITH_ANGLE')
        angsep = sepangle_deg(self.ra_src,self.dec_src,ra,dec)

        # get the phase column
        try:
            phase = ft1file[hduname].data.field(self.phase_colname)
        except KeyError:
            print "\t You need to assign a phase for each event in the fits file. Exiting ..."; exit()

        # get the weight column        
        try:
            weight = ft1file[hduname].data.field(self.weight_colname)
            weight = np.float64(weight)
        except KeyError:
            weight = np.ones(phase.size)
            self.weight_colname = 'WEIGHT'

        tmp = np.rec.fromarrays ([ra,dec,time,energy,evtclass,phase,zenith_angle,angsep,weight],
                                 names='RA,DEC,TIME,ENERGY,EVENT_CLASS,%s,ZENITH_ANGLE,ANGSEP,%s' %(self.phase_colname,self.weight_colname))

        # filter the list of events
        angularcut = np.logical_and( angsep<=self.radius, zenith_angle<=self.zenithcut )
        energycut  = np.logical_and( self.emin<=energy, energy<=self.emax )
        timecut    = np.logical_and( self.tmin<=time, time<=self.tmax )
        eclscut    = np.logical_and( self.eclsmin<=evtclass, evtclass<=self.eclsmax )
        self.eventlist = tmp[np.logical_and(angularcut,np.logical_and(energycut,np.logical_and(timecut,eclscut)))]

    def set_psf_param(self,psfpar0=5.3,psfpar1=0.745,psfpar2=0.09):
        '''Set PSF parameterization: sqrt( (psfpar0x(100/E)^psfpar1)^2 + psfpar2^2 )'''
        self.__psf_selection = [psfpar0,psfpar1,psfpar2]
        print "Parameterization of the PSF has been modified:"
        print "PSF-cut: %.2f x (100/E)^%.2f ++ %.2f (++: in quadrature)\n" %(psfpar0,psfpar1,psfpar2)

    def get_energy_range(self,which=0):
        return self.__energy_range[which][0], self.__energy_range[which][1]

    def set_energy_range(self,which=0,emin=1e2,emax=3e5):
        if emin<self.emin:
            print OKRED + "warning: emin (for histo=%i) cannot be lower than PulsarLightCurve EMIN" %which + ENDC
            emin = self.emin
        if emax>self.emax:
            print OKRED + "warning: emax (for histo=%i) cannot be higher than PulsarLightCurve EMAX" %which + ENDC
            emax = self.emax
        self.__energy_range[which] = [emin,emax]
        print "Energy range for histo=%i has been changed: (%.0f,%.0f) MeV" %(which,emin,emax)

    def get_radius_range(self,which=0):
        return self.__radius_range[which]

    def set_radius_range(self,which=0,radius=100.):
        '''Set the radius (deg) for the histo [which]'''
        if radius>self.radius:
            print OKRED + "warning: radius (for histo=%i) cannot be larger than PulsarLightCurve RADIUS" %which + ENDC 
            radius = self.radius
        self.__radius_range[which] = radius
        print "Radius selection for histo=%i has been changed: %.2f deg" %(which,radius)
        
    def modify_loc(self,ra,dec):
        '''Set the source coordinates (ra,dec)'''
        self.ra_src  = ra
        self.dec_src = dec

    def use_searchpulsation_weights(self, logeref=2., logesig=0.5):
        '''Set the weight of a given event based on Philippe s tool (i.e. SearchPulsation)'''
        angsep = self.eventlist["ANGSEP"]
        energy = self.eventlist["ENERGY"]
        theta = get_theta(self.__psf_selection,energy)
        self.eventlist[self.weight_colname] = get_searchpulsation_weights(energy,angsep,theta,logeref,logesig)
                        
    def get_phases(self,which=0):
        '''Returns an array of pulse phases'''
        return np.asarray(self.pulse_phase[which][:,0][0])

    def get_counts(self,which=0):
        '''Returns an array of counts'''
        histo = self.phaseogram[which]
        return np.asarray([histo.GetBinContent(i+1) for i in range(histo.GetNbinsX()/2)])
        
    def get_weights(self,which=0):
        '''Returns an array of weights'''
        return np.asarray(self.pulse_phase[which][:,1][0])

    def get_times(self,which=0):
        '''Returns an array of times in MJD'''
        return np.asarray(self.pulse_phase[which][:,2][0])
            
    def fill_phaseogram(self, radius=None, nbins=32, phase_range=[0.,2.], phase_shift=0, weight=False):
        '''Fill phaseograms (pulse profiles)
        ===========    ==================================================
        keyword        description
        ===========    ==================================================
        nbins          number of bins in your histogram       [32]
        radius         Maximum radius (deg)                   [FT1 radius]
        phase_range    min and max phase interval             [0,2]
        phase_shift    add a shift to the pulse phase values  [0]
        weight         Use a weight for each photon           [False]
        ===========    ================================================== '''
        
        self.nbins               = nbins
        self.phase_shift         = phase_shift
        self.binmin, self.binmax = phase_range[0], phase_range[1]
        self.weight              = weight
        erange, rrange           = self.__energy_range, self.__radius_range
        ndays                    = 20

        # radius
        if radius is None: radius = self.radius
        else:
            print "(radius): (", radius, ") deg"
            for i, item in enumerate(self.__radius_range):
                self.set_radius_range(i,radius)
        
        if radius>self.radius:
            print OKRED + "warning: radius cannot be larger than PulsarLightCurve RADIUS" + ENDC
            radius = self.radius

        # initialization of histograms
        for item in self.phaseogram:
            item.Reset()
            item.SetBins(nbins*int(self.binmax-self.binmin),self.binmin,self.binmax)
            item.SetMinimum(0.001)

        for item in self.phaseogram2D:
            item.Reset()
            tmin_mjd, tmax_mjd = met2mjd(self.tmin), met2mjd(self.tmax)
            item.SetBins(nbins,self.binmin,self.binmax,int((tmax_mjd-tmin_mjd)/ndays),tmin_mjd,tmax_mjd+30)

        self.pulse_phase = []
        for i in range(self.nhisto):
            self.pulse_phase.append([])

        if self.weight and self.psfcut:
            print OKRED + "You are using the weighting methog and applying an energy-dependent cut!" + ENDC

        # initialization of the event list
        evtlist = self.eventlist[self.eventlist["ANGSEP"]<=radius]

        if self.psfcut:
            evtlist = evtlist[evtlist["ANGSEP"]<get_theta(self.__psf_selection, evtlist["ENERGY"])]

        if phase_shift != 0:
            evtlist[self.phase_colname] += phase_shift
            evtlist[self.phase_colname][evtlist[self.phase_colname]>1] -= 1
            evtlist[self.phase_colname][evtlist[self.phase_colname]<0] += 1
        
        # Fill histograms
        for j in range(len(self.phaseogram)):
            radius_filter = evtlist["ANGSEP"] <= rrange[j]
            energy_filter = np.logical_and( erange[j][0]<=evtlist["ENERGY"], evtlist["ENERGY"]<=erange[j][1] )
            mask = np.logical_and(radius_filter,energy_filter)

            P = evtlist[self.phase_colname][mask]; N = len(P)
            T = met2mjd(evtlist["TIME"][mask])
            W = evtlist[self.weight_colname][mask] if self.weight else np.ones(N)

            if len(P)>0:
                self.phaseogram[j].FillN(N,P,W); self.phaseogram[j].FillN(N,P+1,W)
                self.phaseogram2D[j].FillN(N,P,T,W); self.phaseogram2D[j].FillN(N,P+1,T,W)
                self.pulse_phase[j] += [[P,W,T]]

        # switch to numpy.array
        for i, item in enumerate(self.pulse_phase):
            self.pulse_phase[i] = np.asarray(item)

            # calculate errors for weighted lightcurves
            if self.weight:
                phases = self.get_phases(i)
                weights = self.get_weights(i)
                nmc = 100
                errors = np.empty([self.nbins,nmc])
                for j in xrange(nmc):
                    rweights = weights[np.argsort(np.random.rand(len(phases)))]
                    errors[:,j] = np.histogram(phases,bins=self.nbins,weights=rweights,normed=False)[0]
                errors = np.std(errors,axis=1)
                for ibin, err in enumerate(errors):
                    ibin = ibin+1
                    self.phaseogram[i].SetBinError(ibin,err); self.phaseogram[i].SetBinError(ibin+self.nbins,err)
                    
	# to make a better display due to errorbars
        for histo in self.phaseogram:
            ymax = histo.GetBinContent(histo.GetMaximumBin())
            
            if ymax > 0:
                if self.weight:
                    if ymax>4: ymax*=1.15
                    else: ymax = ymax*(1.05+np.log(ymax)/ymax)+np.sqrt(ymax)
                else: ymax = ymax*(1.05+np.log(ymax)/ymax)+np.sqrt(ymax)
                histo.SetMaximum(int(ymax))
                if histo.GetMaximum()%5 == 0: histo.SetMaximum(histo.GetMaximum()*1.05)
                if histo.GetMaximum()%5 == 1: histo.SetMaximum(histo.GetMaximum()*1.04)
                if histo.GetMaximum()%5 == 2: histo.SetMaximum(histo.GetMaximum()*1.03)
            else:
                histo.SetMaximum(1.1)        


    def get_background(self, which=None, phase_range=[0.,1.], ring_range=[1.,2.], method='ring'):
        '''Return background/bin for a phaseogram.
        ===========   =============================
        keyword       description
        ===========   =============================
        which         phaseogram number    [None]
        phase_range   phase selection      [0,1]
        ring_range    ring dimension(deg)  [1,2]
        method        ring/weight          ["ring"]
        '''
        print "___pending___: evaluating background using %s ..." %method

        phmin, phmax   = phase_range
        erange, rrange = self.__energy_range, self.__radius_range
        
        if self.__psf_selection is None and self.psfcut:
            raise Exception("You must fill histograms before. Exiting...")
            
        if self.radius<ring_range[1]:
            raise Exception("Maximum 'ring' radius is larger than PulsarLightCurve RADIUS. Exiting ...")
        
        # initialization of the list of events
        evtlist = self.eventlist
        theta = get_theta(self.__psf_selection, evtlist["ENERGY"])
        ph = evtlist[self.phase_colname]
        
        evtlist[self.phase_colname] += self.phase_shift
        evtlist[self.phase_colname][evtlist[self.phase_colname]>1] -= 1
        evtlist[self.phase_colname][evtlist[self.phase_colname]<0] += 1                        

        # Calculate background
        bg_level = []
        for N in range(self.nhisto):
            
            roi_events, psf_events, ring_events = 0., 0., 0.
            radius = self.__radius_range[N]
            theta_radmax = get_theta(self.__psf_selection,self.__energy_range[N][0])
        
            if self.psfcut and radius>theta_radmax:
                print "Warning your maximum PSF-cut radius is larger than your maximum radius."
                print "Setting the radius to the maximum PSF-cut radius:", theta_radmax, "deg"
                radius = theta_radmax

            radius_filter = evtlist["ANGSEP"] <= rrange[N]
            energy_filter = np.logical_and(erange[N][0]<=evtlist["ENERGY"], evtlist["ENERGY"]<=erange[N][1] )
            psf_filter    = evtlist["ANGSEP"] < theta if self.psfcut else np.ones(theta.size,dtype=np.bool)
            ring_filter   = np.logical_and(ring_range[0]<=evtlist["ANGSEP"], evtlist["ANGSEP"]<=ring_range[1])
            phase_filter  = np.logical_and(ph>=phmin,ph<=phmax) if phmin<phmax else np.logical_or(ph>=phmin,ph<=phmax)

            if method is 'ring':
                basic_mask  = np.logical_and(energy_filter,phase_filter)
                roi_mask    = np.logical_and(basic_mask,radius_filter)
                roi_events  = roi_mask.sum(dtype=np.float32)
                psf_events  = np.logical_and(roi_mask,psf_filter).sum(dtype=np.float32)
                ring_events = np.logical_and(basic_mask,ring_filter).sum(dtype=np.float32)
                phase_norm  = (phmax-phmin) if phmin<phmax else (1.+phmax-phmin)
                surf_norm   = (power(ring_range[1],2)-power(ring_range[0],2)) / power(radius,2)
                bg_level += [ring_events * ((psf_events/roi_events) / phase_norm / float(self.nbins) / surf_norm)]
            elif method is 'weight':
                mask = np.logical_and(energy_filter,np.logical_and(radius_filter,psf_filter))
                W = evtlist[self.weight_colname][mask]
                if self.weight: bg_level += [(W.sum()-(W**2).sum()) / float(self.nbins)]
                else: bg_level += [(len(W)-W.sum()) / float(self.nbins)]
            else:
                print "Selected method does not exist!"
                bg_level += [0]
                
        if which is None: return bg_level
        else: return [bg_level[which]]

    def add_weight_column(self,colname='WEIGHT',new_filename=None):
        '''Add a column with the weight information in your FT1 file'''

        weights = self.eventlist[self.weight_colname]
        ft1name = new_filename or self.__ft1name
        file = pyfits.open(ft1name)

        # clobber old values
        try:
            file['EVENTS'].data.field(colname)[:] = weights
            print 'Clobbered old WEIGHT column.'
        except KeyError: 
            cols = file['EVENTS'].columns
            newcols = cols.add_col(pyfits.Column(name=colname,format='D',array=weights))
            table = pyfits.new_table(newcols,header=file['EVENTS'].header)
            table.name = 'EVENTS'
            file[1] = table
            
        file.writeto(self.__ft1name,clobber=True)
        file.close()

    def print_psf(self):
        p0,p1,p2 = self.__psf_selection
        print "%.2f x (100/E)^%.2f ++ %.2f (++: in quadrature)" %(p0,p1,p2)

    def print_selection(self):
        print "\n___selection___:"
        print "\tFT1file .............. %s" %self.ft1name
        print "\tpsrname .............. %s" %self.psrname
        print "\tra, dec (deg) ........ %.6f, %.6f" %(self.ra_src,self.dec_src)
        print "\ttmin, tmax (MET,MJD).. %.0f, %.0f - %.4f, %4f" %(self.tmin,self.tmax,met2mjd(self.tmin),met2mjd(self.tmax))
        print "\temin, emax (MeV) ..... %.0f, %.0f" %(self.emin,self.emax)
        print "\tradius (deg) ......... %.1f"  %self.radius
        print "\teclsmin, eclsmax ..... %.0f, %.0f" %(self.eclsmin,self.eclsmax)
        print "\tzenith angle (deg) ... %.0f" %self.zenithcut
        if self.psfcut:
            print "\tPSF-cut ..............",
            self.print_psf()            
        os = 'Yes' if self.weight else 'No'
        print  "\tweighted counts ...... %s" %os

    def print_summary(self):
        self.print_selection()
        print "\n__parameters__| ",
        for i in range(self.nhisto): print "PHASO:" +  str(i), "\t",
        print ""
        for x in range(42): print "- ",
        print "\nemin,emax(MeV)| ",
        for it in range(self.nhisto):
            s = '%(emin)d %(emax)d' %{'emin':self.__energy_range[it][0], 'emax':self.__energy_range[it][1]}
            s += '\t' if len(s)>7 else '\t\t'; print s,
        print "\nradius(deg)   | ",
        for it in range(self.nhisto):
            print '%(radius).1f \t\t' %{'radius':self.__radius_range[it]},
        print "\nnumber of evts| ",
        for histo in self.phaseogram:
            s = "%.0f" %(histo.GetEntries()/2)
            s += '\t' if len(s)>6 else '\t\t'; print s,

        # H-test statistics
        htest = []
        for pulse in self.pulse_phase:
            if len(pulse) > 0.:
                H = hmw(pulse[:,0],pulse[:,1])
                prob = h_sig(H)                
                Hsig = sig2sigma(prob) if prob > 1e-323 else sig2sigma(1e-323)
                htest += [[H,Hsig]]
            else:
                htest += [[0,0]]
        print "\nH-test        | ",
        for item in htest:
            print "%.0f \t \t" %item[0],
        print "\nH-test(sig)   | ",
        for item in htest:
            print "%.1f \t \t" %item[1],
        print "\n\n"

    def load_profile(self, profile, fidpt=0., norm=True, mean_sub=False, ncol=1,
                     ytitle="Radio Flux (au)", comment="", histo=False):
        '''Load radio/xray profiles
        ===========   ==============================================
        keyword       description
        ===========   ==============================================
        profile       radio/x-ray template (ascii)      [necessary]
        fidpt         fiducial point                    [0]
        ncol          phase column number               [1]
        mean_sub      Substract                         [False]
        norm          normalized profile to 1           [True]
        ytitle        ytitle                            ["Radio Flux (au)"]
        comment       comment on profile                [""]
        histo         if "True" plot profile like histo [False]
        '''
        try: phases = np.loadtxt(profile,comments="#")[:,ncol-1]
        except IndexError: phases = np.loadtxt(profile,comments="#")

        phlen = len(phases)            
        phases = np.roll(phases,-int(phlen*fidpt))  # fiducial point
        if mean_sub: phases -= np.mean(phases)
        if norm: phases /= np.max(phases)           # normalization

        if histo:
            template = TH1F()
            template.SetBins(phlen*int(self.binmax-self.binmin),self.binmin,self.binmax)
            for i, p in enumerate(phases):
                template.Fill(float(i)/phlen,p)
                template.Fill(1+float(i)/phlen,p)
            template.SetMinimum(0.01)
            max_histo = template.GetBinContent(template.GetMaximumBin())
            factor = 1.12 + sqrt(max_histo)/max_histo
            template.SetMaximum(int(max_histo*factor))
        else:
            phases = np.append(phases,phases)
            phases = np.append(phases,phases[0])
            template = TGraph(len(phases))
            for i, p in enumerate(phases):
                template.SetPoint(i,float(i)/phlen,p)
            template.GetXaxis().SetLimits(self.binmin,self.binmax)

        return template, ytitle, comment

    def get_phaseogram(self,emin,emax):
        """ Returns a list of phase centers and a list of
            counts for a pulsar in a given energy range. 

            Allow a tolerance of 1 MeV when finding energy range. """
        i = [j for j,erange in enumerate(self.__energy_range) if
             np.allclose([emin,emax], erange, rtol=0, atol=1)]
        if len(i) < 1:
            raise Exception("Cannot find energy range [%g,%g]. Choices are %s" % \
                            (emin,emax,str(self.__energy_range)))
        if len(i) > 1:
            raise Exception("Multiple energy ranges found for [%g,%g]" % (emin,emax))

        p = self.phaseogram[i[0]]

        # The +2 adds one bin at the edge with 0 counts in it, 
        # nice for plotting in matplotlib.
        phase=np.asarray([p.GetBinCenter(i) for i in range(p.GetNbinsX()+2)])
        counts=np.asarray([p.GetBinContent(i) for i in range(p.GetNbinsX()+2)])
        return phase,counts

    def plot_lightcurve( self, nbands=1, xdim=550, ydim=200, background=None, zero_sup=False,
                         inset=None, profile=None, reg=None, color='black', outfile=None,
                         xtitle='Pulse Phase', ytitle='Counts/bin', substitute=True):
        
        '''ROOT function to plot gamma-ray phaseograms + (radio,x-ray)
        ===========   ======================================================
        keyword       description
        ===========   ======================================================
        nbands        number of gamma-ray bands in the figure    [1,..,6]
        xdim, ydim    plot dimensions in pixels                  [550,200]
        profile       radio or x-ray template (use load_profile) [[None]]
        substitute    substitute g-ray profile for r/x profile   [True]
        backgroung    add a background level                     [None]
        zero_sup      active the zero-suppress on the top panel  [false]
        inset         add an inset on the xth panel              [None]
        reg           highlight a phase region                   [None]  
        color         color profile                              [black]
        xtitle        Title for x-axis                           [Pulse Phase]
        ytitle        title for y-axis                           [Counts/bin]
        outfile       output file name
        ===========   ====================================================== '''
        phaseogram = self.phaseogram
        erange = self.__energy_range
        if nbands == 1: substitute = False
        
        root.initialization()
        xdim, ydim = 550, 200    # in pixels
        ydim += 150*nbands
        
        # canvas and pad
        canvas = TCanvas("canvas","canvas",xdim,ydim);
            
        pad = []
        ylow, yup, ystep = 0., 1., 1.
        BottomMarginDefault, TopMarginDefault, RightMarginDefault = 0.12, 0.02, 0.1
                        
        if nbands == 1:
            OffsetX, OffsetY, BottomMarginDefault = 1.1, 1.05, 0.11
        elif nbands == 2:
            OffsetX, OffsetY, BottomMarginDefault = 1.6, 1.6, 0.12
            ylow, ystep = 0.52, 1
        elif nbands == 3:
            OffsetX, OffsetY, BottomMarginDefault = 2.2, 2.1, 0.13
            ylow, ystep = 0.675, 0.315       
        elif nbands == 4:
            OffsetX, OffsetY, BottomMarginDefault = 3.5, 2.6, 0.16
            ylow, ystep = 0.664, 0.21            
        elif nbands == 5:
            OffsetX, OffsetY, BottomMarginDefault = 4.5, 3.1, 0.18
            ylow, ystep = 0.7, 0.17
        elif nbands == 6:
            OffsetX, OffsetY, BottomMarginDefault = 5.5, 3.6, 0.2
            ylow, ystep = 0.78, 0.15
        else:
            raise Exception("Number of energy bands is greater than 6. Not implemented! Exiting ...")            
            
        for N in range(nbands):
            padname = "pad" + str(N)
            pad.append(TPad(padname,padname,0,ylow,1.,yup)); pad[N].Draw()
            yup = ylow if N == 0 else yup - ystep
            ylow = 0 if nbands-2 == N else ylow - ystep
            pad[N].SetBottomMargin(0.); pad[N].SetTopMargin(0.);
            if nbands == N+1: pad[N].SetBottomMargin(BottomMarginDefault)
            
        # Text and other stuff
        TextSize, LabelSize = 16, 16
        text = TText()
        text.SetTextSize(TextSize)
        if self.weight: ytitle = "W. Counts/bin"

        bkglevel = []
        pad[0].SetTopMargin(TopMarginDefault)
        
        # ============== G-RAY PANELS ============== #
        for which in range(nbands):

            pad[which].cd()
                    
            if which+1 == nbands: root.SetHistoAxis(phaseogram[which],xtitle,TextSize,OffsetX,LabelSize,ytitle,TextSize,OffsetY,LabelSize,color=color)
            else: root.SetHistoAxis(phaseogram[which],"",0,0,0,ytitle,TextSize,OffsetY,LabelSize,color=color)

            # zero suppress
            if zero_sup: root.zero_suppress(phaseogram[which])

            # draw histogram
            phaseogram[which].Draw("HIST E")

            # overlap highlighted region
            if reg is not None and which == 0:
                if np.isscalar(reg[0]):
                    boxes = SetHistoBox(phaseogram[which],reg[0],reg[1])
                    [box.Draw() for box in boxes]
                else:
                    boxes = []
                    for r in reg:
                        boxes += [SetHistoBox(phaseogram[which],r[0],r[1])]
                        for box in boxes: [b.Draw() for b in box]

                phaseogram[which].Draw("HIST E SAME")
                gPad.RedrawAxis()   #  force a redraw of the axis
                
            # comment + psrname
            if erange[which][1] > 3e4: ecomment = "> " + str(erange[which][0]/1e3) + " GeV"
            else: ecomment = str(erange[which][0]/1e3) + " - " + str(erange[which][1]/1e3) + " GeV"
            ylevel = root.get_txtlevel(phaseogram[which],0.91)
            text.DrawText(0.1,ylevel,ecomment)
            if which==0: text.DrawText(self.binmax-0.5,ylevel,self.psrname)
            
            if inset == which:   
                phaseogram[-1].SetFillColor(14)
                phaseogram[-1].Draw("same")
                if zero_sup:
                    root.zero_suppress(phaseogram[-1])
                    phaseogram[inset].SetMinimum(phaseogram[-1].GetMinimum())
                text.SetTextColor(14)
                ecomment = "> " + str(erange[-1][0]/1e3) + " GeV"
                ylevel = root.get_txtlevel(phaseogram[which],0.84)
                text.DrawText(0.1,ylevel,ecomment); text.SetTextColor(1)
                
            # draw a background level
            if background is not None:
                for j, bkg in enumerate(background):
                    if j == which:
                        bkglevel += [SetHistoLine(phaseogram[j],bkg,bkg)]
                        bkglevel[j].Draw()
            
        # ============== TEMPLATES ============== #
        if profile is not None:

            for i, prof in enumerate(profile):

                histo, ytitle, comment = prof   # get the profile

                if (nbands == 1 or not substitute) and i == 0:
                    pad[0].cd()
                    overlay = TPad("overlay","",0,0,1,1)
                    overlay.SetBottomMargin(0)
                
                    if nbands == 1:
                        overlay.SetBottomMargin(BottomMarginDefault)
                        overlay.SetRightMargin(RightMarginDefault)
                        pad[0].SetRightMargin(RightMarginDefault)
                        pad[0].SetTicky(0)

                    overlay.SetTopMargin(TopMarginDefault)
                    overlay.SetFillStyle(0); overlay.SetFrameFillStyle(0)
                    overlay.Draw(""); overlay.cd()
                    
                    xmin, xmax = self.binmin, self.binmax
                    ymin, ymax = histo.GetHistogram().GetMinimum()*0.8, histo.GetHistogram().GetMaximum()
                                        
                    hframe = overlay.DrawFrame(xmin,ymin,xmax,ymax)
                    hframe.GetXaxis().SetLabelOffset(99); hframe.GetYaxis().SetLabelOffset(99)
                    hframe.SetTickLength(0,'XY')
                    
                    if len(comment) != 0: ytitle += " (" + comment + ")"
                    axis = TGaxis(xmax,ymin,xmax,ymax,ymin,ymax,510,"+L")
                    # axis.SetLineColor(kRed); axis.SetLabelColor(kRed)
                    if nbands == 1: root.DrawAxis(axis,ytitle,TextSize,OffsetY,LabelSize)
                else:
                    n = -(i+1)
                    BM, TM = pad[n].GetBottomMargin(), pad[n].GetTopMargin()
                    pad[n].Clear(); pad[n].cd()
                    pad[n].SetBottomMargin(BM); pad[n].SetTopMargin(0.02)
                    root.SetHistoAxis(histo,xtitle,TextSize,OffsetX,LabelSize,ytitle,TextSize,OffsetY,LabelSize)

                if histo.__class__.__name__ == 'TGraph':
                    if nbands == 1 or not substitute: histo.Draw("lp")
                    else: histo.Draw("al"); text.DrawText(0.1,histo.GetHistogram().GetMaximum()*0.85,comment)
                elif histo.__class__.__name__ == 'TH1F':
                    histo.Draw(); histo.Draw("Esame")
                    text.DrawText(0.1,histo.GetMaximum()*0.86,comment)
                else:
                    raise Exception("Error in format. Exiting ...")

        # OUTPUT
        if outfile is None: outfile = "%s_fermilat_profile_%s.eps" %(self.psrname,str(nbands))
        canvas.Print(outfile); canvas.Close()

        
    def plot_phase_time( self, which=0, background=None, zero_sup=True, reg=None, xdim=500, ydim=1000,
                         xtitle='Pulse Phase', ytitle='Counts/bin', color='black', outfile=None ):
        '''Plot photon phase vs time
        ===========   ======================================================
        keyword       description
        ===========   ======================================================  
        which         histogram number                           [0]
        backgroung    add a background level on the phaseogram   [None]
        zero_sup      active the zero-suppress on the top panel  [True]
        reg           highlight a phase region                   [None]  
        xdim, ydim    plot dimensions in pixels                  [500,1000]
        xtitle        title for x-axis                           [Pulse Phase]
        ytitle        title for y-axis                           [Counts/bin]
        color         color profile                              ["black"] 
        outfile       output file name
        '''
        root.initialization()
        phaseogram, phaseogram2D = self.phaseogram, self.phaseogram2D
        erange = self.__energy_range
        
        # canvas and pad
        canvas = TCanvas("canvas","canvas",xdim,ydim);
        pad1 = TPad("pad1","pad1",0,0.7,1,1); pad1.Draw()        
        pad2 = TPad("pad2","pad2",0,0,1,0.7); pad2.Draw()

        text = TText()
        TextSize, LabelSize, Offset = 16, 16, 5
        text.SetTextSize(TextSize)
        
        LeftMarginDefault, RightMarginDefault = 0.15, 0.11
        BottomMarginDefault, TopMarginDefault = 0.05, 0.03
        
        # PAD1: pulse profile
        pad1.cd()
        pad1.SetBottomMargin(BottomMarginDefault); pad1.SetTopMargin(TopMarginDefault);
        pad1.SetLeftMargin(LeftMarginDefault); pad1.SetRightMargin(RightMarginDefault)
        
        # title size, title offset, label size
        root.SetHistoAxis(phaseogram[which],"",0,0,0,ytitle,TextSize,Offset,TextSize,color=color)

        if zero_sup:
            root.zero_suppress(phaseogram[which])

        # draw histogram
        phaseogram[which].Draw("HIST E")
        
        if reg is not None:
            listbox = SetHistoBox(phaseogram[which],reg[0],reg[1])
            for box in listbox: box.Draw() 
            phaseogram[which].Draw("Hist E same")
            gPad.RedrawAxis()                 
            
        if background is not None:
            line = TLine(0,background,2,background)
            line.SetLineStyle(2)
            line.Draw()

        tt = "> %.2f GeV" %(erange[which][0]/1e3)
        ylevel = root.get_txtlevel(phaseogram[which],0.91)
        text.DrawText(0.1,ylevel,tt)
        text.DrawText(1.3,ylevel,self.psrname)
           
        # PAD2: phase vs time 
        pad2.cd()
        pad2.SetTopMargin(TopMarginDefault); pad2.SetBottomMargin(0.06)
        pad2.SetLeftMargin(LeftMarginDefault); pad2.SetRightMargin(RightMarginDefault)
        pad2.SetTickx(0)

        root.SetHistoAxis(phaseogram2D[which],xtitle,TextSize,1.5,LabelSize,"Time [MJD]",TextSize,Offset,LabelSize)
        phaseogram2D[which].GetZaxis().SetLabelSize(0.03)
        phaseogram2D[which].Draw("CONT4 Z")

        # superimpose a new pad: significance vs time
        times, phases, weights = self.get_times(which), self.get_phases(which), self.get_weights(which)
        tmin_mjd, tmax_mjd = met2mjd(self.tmin), met2mjd(self.tmax)
        timebins = np.linspace(tmin_mjd,tmax_mjd,20)
        SigTime = TGraph(len(timebins)-1)

        for i, T in enumerate(timebins[1:]):
            time_filter = times<=T
            P = phases[time_filter]
            W = weights[time_filter]
            H = weighted_h_statistic(P,W)
            prob = h_sig(H)
            sig = sig2sigma(prob) if prob > 1e-323 else sig2sigma(1e-323)                            
            SigTime.SetPoint(i,sig,T)
            
        xmin, xmax = SigTime.GetXaxis().GetXmin(), SigTime.GetXaxis().GetXmax()        
        ymin, ymax = phaseogram2D[which].GetYaxis().GetXmin(), phaseogram2D[which].GetYaxis().GetXmax()

        overlay = TPad("overlay","",0,0,1,1)
        overlay.SetBottomMargin(0.06); overlay.SetTopMargin(TopMarginDefault)
        overlay.SetLeftMargin(LeftMarginDefault); overlay.SetRightMargin(RightMarginDefault)
        overlay.SetFillStyle(0); overlay.SetFillColor(0)
        overlay.SetFrameFillStyle(0)
        overlay.Draw(""); overlay.cd()
        
        hframe = overlay.DrawFrame(xmin,ymin,xmax,ymax)
        hframe.GetXaxis().SetLabelOffset(99); hframe.GetYaxis().SetLabelOffset(99)
        hframe.SetTickLength(0,'XY')
        
        SigTime.Draw("L")

        axis = TGaxis(xmin,ymax,xmax,ymax,xmin,xmax,205,"-")
        #axis.SetLineColor(kRed); axis.SetLabelColor(kRed)
        # bug in ROOT - must fix the font to 82 instead 83
        TextSize,Offset,LabelSize = 0.04,0.22,0.03
        root.DrawAxis(axis,"H-test statictics [#sigma]",TextSize,Offset,LabelSize,font=82)
        axis.SetLabelOffset(-0.05)

        # OUTPUT
        if outfile is None: outfile = self.psrname + "_fermilat_phaseogram2D.eps"
        canvas.Print(outfile)

    def plot_ptest_time(self, which=0, xdim=1000, ydim=600, outfile=None):
        '''Plot periodic test results as a funtion of the time
        ===========   ======================================================
        keyword       description
        ===========   ======================================================
        which         histogram number                           [0]     
        outfile       output file name                                
        '''
        
        from scipy.stats import chi2
        root.initialization()

        phases   = get_phases(which)
        nphotons = len(phases)*0.05
        nbins    = int(len(phases)/nphotons)
        htest    = TGraph(nbins)
        z2m_test = TGraph(nbins)

        for i in range(nbins):
            step = nphotons*(i+1)
            z2m_prob = chi2.sf(z2m(phases[0:step])[1],4)
            z2m_test.SetPoint(i,step,sig2sigma(z2m_prob))
            htest.SetPoint(i,step,sig2sigma(h_sig(h_statistic(phases[0:step]))))

        # ==========> canvas and pad
        canvas = TCanvas("canvas","canvas",xdim,ydim);
        TextSize, LabelSize, Offset = 25, 25, 1
        
        pad = TPad("pad","pad",0,0,1,1); pad.Draw()
        pad.cd()
        pad.SetTopMargin(0.05); pad.SetBottomMargin(0.1)
        pad.SetLeftMargin(0.1); pad.SetRightMargin(0.05)
        root.SetHistoAxis(htest,"Number of Photons",TextSize,Offset,LabelSize,"Significance [\sigma]",TextSize,Offset,LabelSize)
        htest.GetHistogram().SetMaximum(htest.GetHistogram().GetMaximum()*1.1)
        htest.SetLineWidth(2); htest.SetLineStyle(5); htest.Draw("apl")
        z2m_test.SetLineWidth(2); z2m_test.Draw("same")

        # significance
        if htest.GetHistogram().GetMaximum()>5: 
            line = TLine(0,5,step,5)
            line.SetLineStyle(4); line.SetLineColor(4)
            line.Draw()

        # legend
        gStyle.SetTextFont(82)
        xl1=0.14; yl1=0.75; xl2=xl1+.2; yl2=yl1+.15
        leg = TLegend(xl1,yl1,xl2,yl2)
        leg.SetHeader(self.psrname)
        leg.AddEntry(htest,"H-test","l")
        leg.AddEntry(z2m_test,"z2m","l")
        leg.SetEntrySeparation(0.1)
        leg.Draw()

        # OUTPUT
        outfile = (self.psrname + "_sig_vs_time.eps") if outfile is None else outfile
        canvas.Print(outfile)
        print ""

    def pulseopt( self, erange=[100,1000], emax=None, ebins=10, rrange=[0.2,2], rbins=10, display=False ):
        '''
        Find the optimum cuts for a ROI (i.e. over radius, energy) based on H-test
        Return ntrials, pre-sig, post-sig, optimal minimum energy, optimal radius
        ===========   =============================================
        keyword       description
        ===========   =============================================
        erange        Minimum Energy threshold(MeV)       [100,1000]
        emax          Maximum Energy (MeV)                [None]
        ebins         Number of energy bins               [10]
        rrange        Minimum and Maximum radius (deg)    [0.2,2]
        rbins         Number of radius bins               [10]
        display       Show results                        [False]
        '''
        # initialization of the list of events
        evtlist = self.eventlist

        if self.psfcut:
            evtlist = evtlist[evtlist["ANGSEP"]<get_theta(self.__psf_selection, evtlist["ENERGY"])]
            thetamax = get_theta(self.__psf_selection, erange[0])
            if rrange[1]>thetamax: rrange[1]=thetamax
            
        energy  = np.logspace(np.log10(erange[0]),np.log10(erange[1]),ebins)
        radius  = np.linspace(rrange[1],rrange[0],rbins)
        if emax is None: emax = self.emax

        ntrials = len(energy)*len(radius)
        sigmax, bestE, bestR = -1, -1, -1

        print "\nSearching for the optimal cut with R[%.1f,%.1f] deg, Emin[%.0f,%.0f] and Emax[%.0f] MeV"\
              %(rrange[0],rrange[1],erange[0],erange[1],emax)
        
        for it_E in energy:
            for it_R in radius:
                emask = np.logical_and(it_E<=evtlist["ENERGY"],evtlist["ENERGY"]<=emax)
                rmask = evtlist["ANGSEP"] <= it_R
                mask = np.logical_and(emask,rmask)
                phases = evtlist[self.phase_colname][mask]
                if len(phases)>0:
                    prob = h_sig(hm(phases))
                    sig = sig2sigma(prob) if prob > 1e-323 else sig2sigma(1e-323)
                if sig > sigmax:
                    sigmax, bestE, bestR = sig, it_E, it_R

        postsig = sigma_trials(sigmax,ntrials)
        if display:
            print "================================"
            print "ntrials ............", ntrials
            print "pre-sig (sigma)..... %.1f" %sigmax
            print "post-sig (sigma) ... %.1f" %postsig
            print "emin, emax (MeV) ... %.0f, %.0f" %(bestE,emax)
            print "radius (deg) ....... %.1f" %bestR
            print "================================"

        return ntrials, sigmax, postsig, bestE, bestR
        
    def toASCII(self, outdir=""):
        '''Copy the pulse phase of each phaseogram into an ascii file
           outdir      output directory
        '''
        erange = self.__energy_range
        filename = join(outdir,self.psrname+"_phaseogram.asc")
        outfile = open(filename,"w")
        outfile.write("# ------------------------------------------------------------------ \n")
        outfile.write("# Private results: LAT Collaboration and PTC ONLY \n")
        outfile.write("# Gamma-Ray Phase Histogram for %s \n" %self.psrname)
        outfile.write("# column: number of counts per energy band [MeV] \n")
        outfile.write("# Nbin   %.0f-%.0f   %.0f-%.0f   %.0f-%.0f   %.0f-%.0f   %.0f-%.0f\n"
                      %(erange[0][0],erange[0][1], erange[1][0],erange[1][1], erange[2][0],erange[2][1],
                        erange[3][0],erange[3][1], erange[4][0],erange[4][1]) )
        outfile.write("# ------------------------------------------------------------------ \n")

        for i in range(self.nbins):
            firsttime = True
            for histo in self.phaseogram:
                if firsttime: outfile.write("%.0f\t\t" %i); firsttime = False
                outfile.write("%.0f\t" %histo.GetBinContent(i+1))
            outfile.write("\n")

        print "INFO:", filename, "has been created." 
        outfile.close()
