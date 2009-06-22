"""
Module implements a binned maximum likelihood analysis with a flexible, energy-dependent ROI based
   on the PSF.

$Header$

author: Matthew Kerr
"""

import numpy as N
from roi_modules import *
from roi_plotting import *
from psmanager import *

 
###====================================================================================================###

class ROIAnalysis(object):

   def init(self):

      self.fit_emin = [100,100] #independent energy ranges for front and back
      self.fit_emax = [5e5,5e5] #0th position for event class 0
      self.threading = False
  
   def __init__(self,ps_manager,bg_manager,spectral_analysis,**kwargs):
      self.init()
      self.__dict__.update(**kwargs)
      if type(self.fit_emin) != type([]): self.fit_emin = [self.fit_emin]*2
      if type(self.fit_emax) != type([]): self.fit_emax = [self.fit_emax]*2
      self.psm  = ps_manager
      self.bgm  = bg_manager
      self.sa   = spectral_analysis
      self.logl = None
      self.setup_bands()

      self.bin_centers = N.sort(list(set([b.e for b in self.bands])))
      self.bin_edges   = N.sort(list(set([b.emin for b in self.bands] + [b.emax for b in self.bands])))

      self.param_state = N.concatenate([m.free for m in self.psm.models])
      self.psm.cache(self.bands)
      self.psm.update_counts(self.bands)

      self.fbands = N.asarray([b for b in self.bands if b.ec == 0])
      self.bbands = N.asarray([b for b in self.bands if b.ec == 1])

      import pp
      self.job_server = pp.Server(2)


   def setup_bands(self):
      
      print 'Extracting events...'
      from collections import deque
      self.bands = deque()
      for band in self.sa.pixeldata.dmap:
         if band.emin() >= self.fit_emin[band.event_class()] and band.emax() < self.fit_emax[band.event_class()]:
            self.bands.append(ROIBand(band,self.sa))
      self.bands = N.asarray(self.bands)

      self.psm.setup_initial_counts(self.bands)
      self.bgm.setup_initial_counts(self.bands)

   
   def reload_data(self):
      counter = 0
      for band in self.sa.pixeldata.dmap:
         if band.emin() >= self.fit_emin[band.event_class()] and band.emax() < self.fit_emax[band.event_class()]:
            self.bands[counter].reload_data(band)
            counter += 1
      self.bgm.reload_data(self.bands)
      self.psm.reload_data(self.bands)
      self.psm.cache(self.bands)

   def logLikelihood(self,parameters,*args):

      bands = self.bands

      self.set_parameters(parameters)

      if self.threading:

         t1 = self.bgm.updateCountsThread(self.fbands,self.bgm)
         t2 = self.bgm.updateCountsThread(self.bbands,self.bgm)
         t1.start();t2.start()

         for t in [t1,t2]:
            t.join()

      else:
      
         self.bgm.update_counts(bands)
      
      self.psm.update_counts(bands)

      ll = 0

      for b in bands:

         ll +=  ( 
                   #integral terms for ROI (go in positive)
                   b.bg_all_counts + b.ps_all_counts

                   -

                   #pixelized terms (go in negative)
                   ((b.pix_counts *
                       N.log(  b.bg_all_pix_counts + b.ps_all_pix_counts )
                   ).sum() if b.has_pixels else 0.)
                )

      return 1e6 if N.isnan(ll) else ll

      
   def bandLikelihood(self,parameters,*args):

      #it would probably be better to parameterize this with an actual flux...
      # (or, at least, a log scale! haha...)
      scale = parameters[0]
      if scale < 0: return 1e6
      band  = args[0]
      which = args[1]

      psc = band.ps_counts[which]

      tot_term = band.bg_all_counts + band.ps_all_counts + (psc*band.overlaps[which])*(scale-1)

      pix_term = (band.pix_counts * N.log(
                  band.bg_all_pix_counts + band.ps_all_pix_counts + (psc*band.ps_pix_counts[:,which]*(scale-1))
                 )).sum() if band.has_pixels else 0.

      return tot_term - pix_term
   
   def spatialLikelihood(self,skydir,which=0):
      """Calculate log likelihood as a function of position a point source.
      
         which   -- index of point source; default to central
                    ***if localizing non-central, ensure ROI is large enough!***
      """
      
      ro = ROIOverlap()
      rd = self.sa.roi_dir
      ll = 0

      from skymaps import PsfSkyFunction

      for i,band in enumerate(self.bands):
   
         sigma,gamma,en,exp,pa = band.s,band.g,band.e,band.exp,band.b.pixelArea()
         exposure_ratio        = exp.value(skydir,en)/exp.value(rd,en)
         psf                   = PsfSkyFunction(skydir,gamma,sigma)
         
         overlap               = ro(band,rd,skydir) * exposure_ratio * band.solid_angle / band.solid_angle_p
         ool                   = band.overlaps[which]
         psc                   = band.ps_counts[which]

         tot_term              = band.bg_all_counts + band.ps_all_counts + psc * (overlap - ool)

         if band.has_pixels:

            ps_pix_counts = N.asarray(psf.wsdl_vector_value(band.wsdl))*((pa/(2*N.pi*sigma**2))*exposure_ratio)

            pix_term = (band.pix_counts * N.log
                           (
                           band.bg_all_pix_counts + 
                           band.ps_all_pix_counts + 
                           psc*(ps_pix_counts - band.ps_pix_counts[:,which])
                           )
                       ).sum()

         else:
            pix_term = 0

         ll += tot_term - pix_term

      return ll


   def parameters(self):
      """Merge parameters from background and point sources."""
      return N.asarray(self.bgm.parameters()+self.psm.parameters())

   def get_parameters(self):
      """Support for hessian calculation in specfitter module."""
      return self.parameters()

   def set_parameters(self,parameters):
      """Support for hessian calculation in specfitter module."""
      self.bgm.set_parameters(parameters,current_position=0)
      self.psm.set_parameters(parameters,current_position=len(self.bgm.parameters()))
      self.fit_parameters = parameters
   
   def fit(self,method='simplex', tolerance = 1e-8, save_values = True, do_background=True):
      """Maximize likelihood and estimate errors.

         method -- ['powell'] fitter; 'powell' or 'simplex'
      """
      #cache frozen values
      param_state = N.concatenate([m.free for m in self.psm.models])
      if not N.all(param_state == self.param_state):
         self.psm.cache(self.bands)
         self.param_state = param_state
      self.bgm.cache()
      
      print 'Performing likelihood maximization...'
      from scipy.optimize import fmin,fmin_powell
      minimizer  = fmin_powell if method == 'powell' else fmin
      f = minimizer(self.logLikelihood,self.parameters(),full_output=1,\
                    maxiter=10000,maxfun=20000,ftol=tolerance,xtol=tolerance)
      print 'Function value at minimum: %.8g'%f[1]
      if save_values:
         self.set_parameters(f[0])
         self.__set_error__(do_background)
         self.logl = -f[1]
      return -f[1] 

   def __set_error__(self,do_background=True):
      from specfitter import SpectralModelFitter
      from numpy.linalg import inv
      n = len(self.bgm.parameters())
      hessian = SpectralModelFitter.hessian(self,self.logLikelihood) #does Hessian for free parameters

      try:
         if not do_background: raise Exception
         print 'Attempting to invert full hessian...'
         cov_matrix = inv(hessian)
         self.bgm.set_covariance_matrix(cov_matrix,current_position=0)
         self.psm.set_covariance_matrix(cov_matrix,current_position=n)
      except:
         print 'Skipping full Hessian inversion, trying point source parameter subset...'
         try:
            cov_matrix = inv(hessian[n:,n:])
            self.psm.set_covariance_matrix(cov_matrix,current_position=0)
         except:
            print 'Error in calculating and inverting hessian.'

   def __str__(self,verbose=False):
      bg_header  = '======== BACKGROUND FITS =============='
      ps_header  = '======== POINT SOURCE FITS ============'
      return '\n\n'.join([ps_header,self.psm.__str__(verbose),bg_header,self.bgm.__str__()])
         
   def TS(self):
      """Calculate the significance of the central point source."""

      save_params = self.parameters().copy() #save parameters
      m = self.psm.models[0]
      m.p[0] = -200 #effectively 0 flux
      save_free = N.asarray(m.free).copy()
      self.logLikelihood(self.parameters()) #update counts before freezing
      for i in xrange(len(m.free)): m.free[i] = False #freeze all parameters
      alt_ll = self.fit(save_values = False)
      for i in xrange(len(m.free)): m.free[i] = save_free[i] #unfreeze appropriate
      self.psm.cache(self.bands)
      ll = -self.logLikelihood(save_params) #reset predicted counts
      return -2*(alt_ll - ll)

   def localize(self,tolerance=1e-4,update=False,which=0):
      """Localize a source using an elliptic approximation to the likelihood surface.

         tolerance -- maximum difference in degrees between two successive best fit positions
         update    -- if True, update localization internally, i.e., recalculate point source contribution
                      [NOT IMPLEMENTED]
         which     -- index of point source; default to central [NOT IMPLEMENTED]
                      ***if localizing non-central, ensure ROI is large enough!***
      """
      import quadform
      rl = ROILocalizer(self)
      l  = quadform.Localize(rl,verbose = False)
      ld = SkyDir(l.dir.ra(),l.dir.dec())
      for i in xrange(5):
         l.fit(update=True)
         diff = l.dir.difference(ld)*180/N.pi
         print 'Difference from previous fit: %.5f deg'%(diff)
         if diff < tolerance:
            print 'Converged!'
            break
         ld = SkyDir(l.dir.ra(),l.dir.dec())

      self.qform   = l
      self.ldir    = l.dir
      self.lsigma  = l.sigma
      self.rl      = rl


   def __call__(self,v):
      
      pass #make this a TS map? negative -- spatialLikelihood does it, essentially