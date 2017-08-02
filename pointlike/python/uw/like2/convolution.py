"""
Convolution interface for like2
Extends classes from uw.utilities 


$Header$
author:  Toby Burnett
"""
import os, pickle, zipfile 
import numpy as np
import pandas as pd
from uw.utilities import keyword_options
from uw.utilities import convolution as utilities_convolution

import skymaps #from Science Tools: for SkyDir 

class FillMixin(object):
    """A Mixin class for like2 convolution, to replace functions in utilities.convolution
    """
    def fill(self, skyfun):
        """ Evaluate skyfun along the internal grid and return the resulting array.
        (Identical to superclass, except skyfun can be either a python functor or a 
        C++ SkySkySpectrum)
        """
        v = np.empty(self.npix*self.npix)
        if isinstance(skyfun, skymaps.SkySpectrum):
            skymaps.PythonUtilities.val_grid(v,self.lons,self.lats,self.center,skyfun)
        else:
            def pyskyfun(u):
                return skyfun(skymaps.SkyDir(skymaps.Hep3Vector(u[0],u[1],u[2])))
            skymaps.PythonUtilities.val_grid(v,self.lons,self.lats,self.center,
                skymaps.PySkyFunction(pyskyfun))
        return v.reshape([self.npix,self.npix])
        
    def bg_fill(self, exp, dm, cache=None, ignore_nan=False):
        """ Evaluate product of exposure and diffuse map on the grid
        exp : SkyFunction for exposure
        dm  : [SkyFuntion for diffuse map | None]
            If None, expect predetermined values in cache, which may be an array or a scalar
        """
        #print 'filling with product of exposure "%s" model "%s"' % (exp, dm)
        
        if dm is None:
            assert cache is not None, 'Logic error'
            self.bg_vals = self.fill(exp) * cache
        else:
            def exp_dm(skydir):
                    return exp(skydir)*dm(skydir)
            self.bg_vals = self.fill(exp_dm)
    
        #self.bg_vals = self.fill(exp) * (self.fill(dm) if cache is None else cache) #product of exposure and map
        #self.dm_vals = self.fill(dm) #temporary
        #self.exp_vals = self.fill(exp)
        # check for nans, replace with zeros if not full ROI
        nans = np.isnan(self.bg_vals)
        if np.all(nans):
            if dm is None: raise Exception('Cache entry has all nans: %s'%cache)
            raise Exception('Diffuse source %s has no overlap with ROi' % dm.filename)
        if np.any(nans) and ignore_nan:
            self.bg_vals[nans]=0
            
    def psf_fill(self, psf):
        """ Evaluate PSF on the grid
        """
        #print 'filling with psf %s' % psf
        psf_vals = psf(self.dists).reshape([self.npix,self.npix])
        self.psf_vals = psf_vals / psf_vals.sum()
        
    def set_npix(self, psf, edge=0, r_multi=1.2, r_max=20):
        """ modify the npix with
            psf : PSF object
            edge: float --Source size (degrees)
            r_multi   float multiple of r95 to set max dimension of grid
            r_max     float an absolute maximum (half)-size of grid (deg)
            """
        r95 = psf.inverse_integral(95)
        rad = r_multi*r95 + edge
        rad = max(min(r_max,rad),edge+2.5)
        npix = int(round(2*rad/self.pixelsize))
        npix += (npix%2 == 0)
        return npix


class ShowMixin(object):
    """ A mixin class to add or replace show methods
    """
    def show_vals(self, vals=None, ax=None, roi_radius=5, roi_dir=None, colorbar=True, npix=None, **kw):
        """Make a display.
        vals : 2-d array of float
            generated by the fill method; expect to be npix x npix
        npix : [int | None]
            if int, override self.npix to for central npix x npix
        """
        import pylab as plt
        if ax is None: fig,ax=plt.subplots()
        if vals is None: vals = self.cvals
        if npix is not None and npix!=self.npix:
            delta = (self.npix-npix)/2
            assert delta>0, 'npix not >= self.npix'
            tvals = vals[delta:delta+npix, delta:delta+npix]
        else: 
            npix=self.npix; tvals = vals
        if roi_radius is not None:
            if roi_dir is None: roi_dir = self.center
            circle = plt.Circle(self.pix(roi_dir),roi_radius/self.pixelsize, color='grey', lw=2,fill=False)
            ax.add_artist(circle)

        v = ax.imshow( tvals.transpose()[::-1],  interpolation='nearest', **kw)
        marker = float(npix)/2
        ax.axvline(marker,color='k')
        ax.axhline(marker,color='k')
        if colorbar: 
            cb = plt.colorbar(v, shrink=0.8)
        def scale(x, factor=1.0):
            return x*factor/self.pixelsize+self.npix/2.
        r = np.arange(-8,9,4)
        ax.set_xticks(scale(r))
        ax.set_xticklabels(map(lambda x:'%.0f'%x ,r))
        ax.set_yticks(scale(r, -1))
        ax.set_yticklabels(map(lambda x:'%.0f'%x ,r))
        return ax.figure
            
    def show(self, roi_radius=None,roi_dir=None, **kwargs):
        """Three subplots: PSF, raw, convolved"""
        import pylab as plt
        from matplotlib.colors import LogNorm
        title = kwargs.pop('title', None)
        if hasattr(self, 'band'):
            roi_radius = self.band.radius
            roi_dir = self.band.sd
        fig, axx = plt.subplots(1,3, figsize=(10,3), sharex=True, sharey=True)
        plt.subplots_adjust(wspace=0.05)
        if hasattr(self, 'psf_vals'):
            axx[0].imshow(self.psf_vals,interpolation='nearest')
        vmax = self.bg_vals.max()
        norm = LogNorm(vmax=vmax, vmin=vmax/1e3)
        marker = float(self.npix)/2
        for ax,what in zip(axx[1:], (self.bg_vals, self.cvals)  ):
            what[what==0]=vmax/1e6
            ax.imshow(what.transpose()[::-1], norm=norm, interpolation='nearest')
            ax.axvline(marker,color='grey')
            ax.axhline(marker,color='grey')
            if roi_radius is not None:
                if roi_dir is None: roi_dir = self.center
                circle = plt.Circle(self.pix(roi_dir),roi_radius/self.pixelsize, color='grey', lw=2,fill=False)
                ax.add_artist(circle)
        axx[0].set_aspect(1.0)
        if title is not None:
            plt.suptitle(title,fontsize='small')
            
        return fig

class ConvolvableGrid(FillMixin, ShowMixin, utilities_convolution.BackgroundConvolution):
    """ Convolution used by response classes. This subclass uses the mixin classes defined here to:
    
      1) changes the default for a bounds error (to check)
      2) Replaces fill method with version that works for python class
      3) provides useful show methods
      """
    defaults =(
        ('pixelsize', 0.1, 'Size of pixels to use for convolution grid'),
        ('npix',      201, 'Number of pixels (must be an odd number'),
        )

    @keyword_options.decorate(defaults)
    def __init__(self, center, **kwargs):
        """ center -- a SkyDir giving the center of the grid on which to convolve bg
            kwargs are passed to Grid.
        """
        keyword_options.process(self, kwargs)
        defaults=dict(bounds_error=False)
        defaults.update(kwargs)
        # note do not use code in superclass needing psf, diffuse function
        super(ConvolvableGrid, self).__init__(center, None, None, **defaults)
        self.center = center
        
    def __repr__(self):
        return '%s.%s: center %s npix %d pixelsize %.2f' %(
            self.__module__,self.__class__.__name__, self.center, self.npix, self.pixelsize)

def spherical_harmonic(f, lmax, thetamax=45):
    """ Calculate spherical harmonics for a function f, l<=lmax
    thetamax : float, optionial. units degrees
        integral over costheta is in principle from -1 (180 deg) to +1
        but the function may be limited to much smaller than that
    """
    from scipy.integrate import quad
    from scipy.special import legendre
    func = lambda x,n : f(np.sqrt(2*(1-x))) * legendre(n)(x)
    ctmin = np.cos(np.radians(thetamax))
    G = lambda n :quad(func, ctmin,1, args=n)[0] #note lower limit not -1
    norm = G(0)
    return np.array([G(n) for n in range(lmax+1)])/norm

def convolve_healpix(input_map, func ):
    """
    Convolve a HEALPix map with a function
    input_map : array of float
        a HEALPix array, RING indexing, nside a power of 2
    func : The function of an integer el
        returns the amplitude for spherical harmonic el
        example: for a Gaussian with sigma in radians: 
          lambda el : np.exp(-0.5 * (el * (el + 1)) * sigma**2)
          
    Returns: the convolved map
    """
    import healpy
    nside = int(np.sqrt(len(input_map)/12))
    assert 12*nside**2 == len(input_map),'Bad length'
    alm = healpy.map2alm(input_map);
    lmax = healpy.Alm.getlmax(len(alm))
    if lmax < 0:
        raise TypeError('Wrong alm size for the given '
                        'mmax (len(alms[%d]) = %d).'%(ialm, len(alm)))
    ell = np.arange(lmax + 1.)
    fact = np.array([func(x) for x in ell])
    
    healpy.almxfl(alm, fact, inplace=True)
    return healpy.alm2map(alm, nside=nside, verbose=False)

class SphericalHarmonicContent(object):
    """ This class is a functor, defining a function of the spherical harmonic index
    The integral is expensive: it samples the function
    """

    def __init__(self, f, lmax, thetamax=45., tolerance=1e-3):
        """Evaluate spherical harmonic content of a funtion of theta

        f : function
        lmax : int
        thetamax : limit integral over cos theta
        tolerance : paramter to adjust points to evaluate
        """
        from scipy.integrate import quad
        from scipy.special import legendre
        
        func = lambda x,n : f(np.sqrt(2*(1-x))) * legendre(n)(x)
        ctmin = np.cos(np.radians(thetamax))
        norm=1
        self.G = lambda n :quad(func, ctmin,1, args=n)[0]/norm #note lower limit not -1
        norm=self.G(0)
        self.lmax = lmax
        self.fun=None
        self.values = []
        self.addpoint(0)
        self.addpoint(lmax)
        if tolerance is not None:
            self._approximate(tolerance)

    def addpoint(self, el, test=False):
        if test:
            cvalue = self(el)
        self.values.append((el, self.G(el)))
        if self.fun is not None:
            self._setup_interpolation()
        if test: return self(el)/cvalue -1   
             
    def _setup_interpolation(self):
        from scipy import interpolate
        t = np.array(self.values, dtype = [('el', float), ('value',float)])
        s = np.sort(t, order='el')
        self.el=s['el']; self.value=s['value']
        self.fun = interpolate.interp1d(s['el'],s['value'], 
                                        kind='quadratic' if len(self.values)>2 else 'linear')
        
    def __call__(self, ell):
        """
        ell : value or array of int
        returns the interpolating function output
        """
        if self.fun is None:
            self._setup_interpolation()
        return self.fun(ell)
    
    def _approximate(self, tolerance=1e-3, quiet=True):
        el=int(self.lmax/2) 
        done = False
        while el>2 and not done :
            x = self.addpoint(el,True)
            if not quiet:
                print '{}:{:.4f}'.format(el, x)
            done = abs(x)<1e-3
            el= el//2

    def plot(self, title='', ax=None):
        import matplotlib.pyplot as plt
        if ax is None: fig,ax = plt.subplots()
        ax.plot(self(np.arange(self.lmax+1)), '--', label='interpolation')
        ax.plot(self.el,self.value,'o', label='evaluated')
        ax.set_xlabel('$l$');
        ax.set_ylim((0,1.05))
        ax.set_title(title)
        ax.legend();