"""
A module implementing a mixture model of LCPrimitives to form a
normalized template representing directional data.
$Header$

author: M. Kerr <matthew.kerr@gmail.com>

"""

import numpy as np
from copy import deepcopy
from lcnorm import NormAngles
from lcprimitives import *

class LCTemplate(object):
    """Manage a lightcurve template (collection of LCPrimitive objects).
   
       IMPORTANT: a constant background is assumed in the overall model, 
       so there is no need to furnish this separately.

       The template is such that 
    """

    def __init__(self,primitives,norms=None):
        """ primitives -- a list of LCPrimitive instances
            norms -- either an instance of NormAngles, or a tuple of
                relative amplitudes for the primitive components."""
        self.primitives = primitives
        self.shift_mode = np.any([p.shift_mode for p in self.primitives])
        if norms is None:
            norms = np.ones(len(primitives))/len(primitives)
        self.norms = norms if isinstance(norms,NormAngles) else \
                     NormAngles(norms)
        if len(primitives) != len(self.norms):
            raise ValueError('Must provide a normalization for each component.')

    def is_energy_dependent(self):
        return False

    def __getitem__(self,index): return self.primitives[index]
    def __setitem__(self,index,value): self.primitives[index]=value
    def __len__(self): return len(self.primitives)
    def copy(self):
        prims = [deepcopy(x) for x in self.primitives]
        return self.__class__(prims,self.norms.copy())

    def set_parameters(self,p,free=True):
        start = 0
        params_ok = True
        for prim in self.primitives:
            n = len(prim.get_parameters(free=free))
            params_ok = prim.set_parameters(p[start:start+n],free=free) and params_ok
            start += n
        self.norms.set_parameters(p[start:],free)
        return params_ok

    def set_errors(self,errs):
        start = 0
        for prim in self.primitives:
            n = len(prim.get_parameters())
            prim.errors = np.zeros_like(prim.p)
            prim.errors[prim.free] = errs[start:start+n]
            start += n
        self.norms.set_errors(errs[start:])

    def get_parameters(self,free=True):
        return np.append(np.concatenate( [prim.get_parameters(free) for prim in self.primitives]) , self.norms.get_parameters(free))

    def get_gaussian_prior(self):
        locs,widths,mods,enables = [],[],[],[]
        for prim in self.primitives:
            l,w,m,e = prim.get_gauss_prior_parameters()
            #locs.append(l[prim.free])
            #widths.append(w[prim.free])
            #mods.append(m[prim.free])
            #enables.append(e[prim.free])
            locs.append(l)
            widths.append(w)
            mods.append(m)
            enables.append(e)
        t = np.zeros_like(self.norms.get_parameters())
        locs = np.append(np.concatenate(locs),t)
        widths = np.append(np.concatenate(widths),t)
        mods = np.append(np.concatenate(mods),t.astype(bool))
        enables = np.append(np.concatenate(enables),t.astype(bool))
        return GaussianPrior(locs,widths,mods,mask=enables)

    def get_bounds(self):
        b1 = np.concatenate([prim.get_bounds() for prim in self.primitives])
        b2 = self.norms.get_bounds()
        return np.concatenate((b1,b2)).tolist()

    def set_overall_phase(self,ph):
        """Put the peak of the first component at phase ph."""
        if self.shift_mode:
            self.primitives[0].p[0] = ph
            return
        shift = ph - self.primitives[0].get_location()
        for prim in self.primitives:
            new_location = (prim.get_location() + shift)%1
            prim.set_location(new_location)

    def get_location(self):
        return self.primitives[0].get_location()

    def get_amplitudes(self,log10_ens=3):
        """ Return maximum amplitude of a component."""
        ampls = [p(p.get_location(),log10_ens) for p in self.primitives]
        return self.norms(log10_ens)*np.asarray(ampls)

    def get_code(self):
        """ Return a short string encoding the components in the template."""
        return '/'.join((p.shortname for p in self.primitives))

    def norm(self):
        return self.norms.get_total()

    def integrate(self,phi1,phi2,log10_ens,suppress_bg=False):
        norms = self.norms(log10_ens)
        t = norms.sum(axis=0)
        dphi = (phi2-phi1)
        rvals = np.zeros_like(t)
        for n,prim in zip(norms,self.primitives):
            rvals += n*prim.integrate(phi1,phi2,log10_ens)
        rvals.sum(axis=0)
        if suppress_bg: 
            return rvals / t
        return (1-t)*dphi + rvals

    """
    # TODO -- sig compat
    def integrate(self,phi1,phi2, suppress_bg=False):
        norms = self.norms()
        t = norms.sum()
        dphi = (phi2-phi1)
        if suppress_bg: return sum( (n*prim.integrate(phi1,phi2) for n,prim in zip(norms,self.primitives)) )/t

        return (1-t)*dphi + sum( (n*prim.integrate(phi1,phi2) for n,prim in zip(norms,self.primitives)) )
    """

    def cdf(self,x,log10_ens=3):
        return self.integrate(0,x,log10_ens,suppress_bg=False) 

    def max(self,resolution=0.01):
        return self(np.arange(0,1,resolution)).max()

    def __call__(self,phases,log10_ens=3,suppress_bg=False):
        """
        norms = self.norms()
        if (not hasattr(phases,'shape')):
            phases = np.asarray([phases])
        rval = np.zeros_like(phases)
        for n,prim in zip(norms,self.primitives):
            rval += n*prim(phases)
        if suppress_bg: return rval/norms.sum()
        return (1-norms.sum()) + rval
        """
        norms = self.norms(log10_ens)
        rval = np.zeros_like(phases)
        for n,prim in zip(norms,self.primitives):
            rval += n*prim(phases,log10_ens)
        if suppress_bg: return rval/norms.sum(axis=0)
        return (1-norms.sum(axis=0)) + rval

    def single_component(self,index,phases,log10_ens=3):
        """ Evaluate a single component of template."""
        n = self.norms(log10_ens)[index]
        return self.primitives[index](phases,log10_ens)*n

    def gradient(self,phases,log10_ens=3,free=True):
        r = np.empty([len(self.get_parameters(free=free)),len(phases)])
        c = 0
        norms = self.norms()
        prim_terms = np.empty([len(phases),len(self.primitives)])
        for i,(norm,prim) in enumerate(zip(norms,self.primitives)):
            n = len(prim.get_parameters(free=free))
            r[c:c+n,:] = norm*prim.gradient(phases,free=free)
            c += n
            prim_terms[:,i] = prim(phases)-1
        # handle case where no norm parameters are free
        if (c == r.shape[0]): return r
        m = self.norms.gradient(free=free)
        #r[c:,:] = (prim_terms*m).sum(axis=1)
        for j in xrange(m.shape[0]):
            r[c,:] = (prim_terms*m[:,j]).sum(axis=1)
            c += 1
        return r

    def approx_gradient(self,phases,log10_ens,eps=1e-5):
        return approx_gradient(self,phases,log10_ens,eps=eps)

    def check_gradient(self,atol=1e-8,rtol=1e-5,quiet=False):
        return check_gradient(self,atol=atol,rtol=rtol,quiet=quiet)

    def delta(self,index=None):
        """ Return radio lag -- reckoned by default as the posittion of the            first peak following phase 0."""
        if (index is not None) and (index<=(len(self.primitives))):
            return self[index].get_location(error=True)
        return self.Delta(delta=True)

    def Delta(self,delta=False):
        """ Report peak separation -- reckoned by default as the distance
            between the first and final component locations.
            
            delta [False] -- if True, return the first peak position"""
        if len(self.primitives)==1: return -1,0
        prim0,prim1 = self[0],self[-1]
        for p in self.primitives:
            if p.get_location() < prim0.get_location(): prim0 = p
            if p.get_location() > prim1.get_location(): prim1 = p
        p1,e1 = prim0.get_location(error=True) 
        p2,e2 = prim1.get_location(error=True)
        if delta: return p1,e1
        return (p2-p1,(e1**2+e2**2)**0.5)

    def _sorted_prims(self):
        def cmp(p1,p2):
            if   p1.p[-1] <  p2.p[-1]: return -1
            elif p1.p[-1] == p2.p[-1]: return 0
            else: return 1
        return sorted(self.primitives,cmp=cmp)

    def __str__(self):
        #prims = self._sorted_prims()
        prims = self.primitives
        s0 = str(self.norms)
        s1 = '\n\n'+'\n\n'.join( ['P%d -- '%(i+1)+str(prim) for i,prim in enumerate(prims)] ) + '\n'
        s1 +=  '\ndelta   : %.4f +\- %.4f'%self.delta()
        s1 +=  '\nDelta   : %.4f +\- %.4f'%self.Delta()
        return s0+s1

    def prof_string(self,outputfile=None):
        """ Return a string compatible with the format used by pygaussfit.
            Assume all primitives are gaussians."""
        rstrings = []
        dashes = '-'*25
        norm,errnorm = 0,0
      
        for nprim,prim in enumerate(self.primitives):
            phas = prim.get_location(error=True)
            fwhm = 2*prim.get_width(error=True,hwhm=True)
            ampl = [self.norms()[nprim],0]
            norm += ampl[0]
            errnorm += (ampl[1]**2)
            for st,va in zip(['phas','fwhm','ampl'],[phas,fwhm,ampl]):
                rstrings += ['%s%d = %.5f +/- %.5f'%(st,nprim+1,va[0],va[1])]
        const = 'const = %.5f +/- %.5f'%(1-norm,errnorm**0.5)
        rstring = [dashes] + [const] + rstrings + [dashes]
        if outputfile is not None:
            f = open(outputfile,'w')
            f.write('# gauss\n')
            for s in rstring: f.write(s+'\n')
        return '\n'.join(rstring)
       
    def random(self,n,weights=None,return_partition=False):
        """ Return n pseudo-random variables drawn from the distribution 
            given by this light curve template.

            Uses a mulitinomial to divvy the n phases up amongs the various
            components, which then each generate MC phases from their own
            distributions.

            If a vector of weights is provided, the weight in interpreted
            as the probability that a photon comes from the template.  A
            random check is done according to this probability to
            determine whether to draw the photon from the template or from
            a uniform distribution.
        """

        # compatibility with energy-dependent calls
        if hasattr(n,'__len__'):
            n = len(n)

        # edge case of uniform template
        if len(self.primitives)==0:
            if return_partition: return np.random.rand(n),[n]
            return np.random.rand(n)

        n = int(round(n))
        norms = self.norms()
        norms = np.append(norms,[1-sum(norms)])
        rvals = np.empty(n)
        partition = np.empty(n) # record the index of each component
        if weights is not None:
            # perform a trial to see if each photon is from bg or template
            if len(weights) != n:
                raise ValueError('Provided weight vector does not provide a weight for each photon.')
            t = np.random.rand(n)
            m = t <= weights
            t_indices = np.arange(n)[m] # indices to draw from templates (not bg)
            n = m.sum()
            rvals[~m] = np.random.rand(len(m)-n) # assign uniform phases to the bg photons
            partition[~m] = len(norms)-1 # set partition to bg component (last)
        else:
            t_indices = np.arange(n)

        # TODO -- faster implementation for single component case

        # multinomial implementation -- draw from the template components
        a = np.argsort(norms)[::-1]
        boundaries = np.cumsum(norms[a])
        components = np.searchsorted(boundaries,np.random.rand(n))
        counter = 0
        for mapped_comp,comp in zip(a,np.arange(len(norms))):
            n = (components==comp).sum()
            idx = t_indices[counter:counter+n]
            if mapped_comp == len(norms)-1: # uniform
                rvals[idx] = np.random.rand(n)
            else:
                rvals[idx] = self.primitives[mapped_comp].random(n)
            partition[idx] = mapped_comp
            counter += n
        if return_partition:
            return rvals,partition
        return rvals

    def swap_primitive(self,index,ptype=LCLorentzian):
       """ Swap the specified primitive for a new one with the parameters
           that match the old one as closely as possible."""
       self.primitives[index] = convert_primitive(self.primitives[index],ptype)

    def delete_primitive(self,index):
        """ [Convenience] -- return a new LCTemplate with the specified
            LCPrimitive removed and renormalized."""
        norms,prims = self.norms,self.primitives
        if len(prims)==1:
            raise ValueError('Template only has a single primitive.')
        if index < 0: index += len(prims)
        nprims = [deepcopy(prims[i]) for i in xrange(len(prims)) if i!=index]
        nnorms = np.asarray([norms()[i] for i in xrange(len(prims)) if i!= index])
        norms_free = [norms.free[i] for i in xrange(len(prims)) if i!=index]
        lct = LCTemplate(nprims,nnorms*norms().sum()/nnorms.sum())
        lct.norms.free[:] = norms_free
        return lct

    def order_primitives(self,indices,zeropt=0,order_by_amplitude=False):
        """ Order the primitives specified by the indices by position.
            x0 specifies an alternative zeropt.
            
            If specified, the peaks will instead be ordered by descending 
            maximum amplitude."""
        def dist(index):
            p = self.primitives[index]
            if order_by_amplitude:
                a = self.get_amplitudes()
                return a.max()-a[index]
            d = p.get_location()-zeropt
            return d if (d > 0) else d+1
        if not hasattr(indices,'__len__'):
            raise TypeError('indices must specify a list or array of indices')
        if len(indices)<2:
            print 'Found fewer than 2 indices, returning.'
            return
        norms,prims = self.norms(),self.primitives
        norms_free = self.norms.free.copy()
        for i in indices:
            x0 = dist(i)
            x1 = x0
            swapj = i
            for j in indices[i+1:]:
                dj = dist(j)
                if dj<x1:
                    x1 = dj
                    swapj = j
            if x1 < x0:
                j = swapj
                prims[i],prims[j] = prims[j],prims[i]
                norms[i],norms[j] = norms[j],norms[i]
                norms_free[i],norms_free[j] = norms_free[j],norms_free[i]
        self.norms = NormAngles(norms) # this may be fragile
        self.norms.free[:] = norms_free

    def get_fixed_energy_version(self,log10_en=3):
        return self

    def get_eval_string(self):
        """ Return a string that can be "eval"ed to make a cloned set of
            primitives and template. """
        ps = '\n'.join(('p%d = %s'%(i,p.eval_string()) for i,p in enumerate(self.primitives)))
        prims = '[%s]'%(','.join( ('p%d'%i for i in xrange(len(self.primitives)))))
        ns = 'norms = %s'%(self.norms.eval_string())
        s = '%s(%s,norms)'%(self.__class__.__name__,prims)
        return s

    def closest_to_peak(self,phases):
        return min((p.closest_to_peak(phases) for p in self.primitives))

    def mean_value(self,phases,log10_ens=None,weights=None,bins=20):
        """ Compute the mean value of the profile over the codomain of 
            phases.  Mean is taken over energy and is unweighted unless
            a set of weights are provided."""
        if (log10_ens is None) or (not self.is_energy_dependent()):
            return self(phases)
        if weights is None:
            weights = np.ones_like(log10_ens)
        edges = np.linspace(log10_ens.min(),log10_ens.max(),bins+1)
        w = np.histogram(log10_ens,weights=weights,bins=edges)
        rvals = np.zeros_like(phases)
        for weight,en in zip(w[0],(edges[:-1]+edges[1:])/2):
            rvals += weight*self(phases,en)
        rvals /= w[0].sum()
        return rvals

    def mean_single_component(self,index,phases,log10_ens=None,weights=None,bins=20):
        prim = self.primitives[index]
        if (log10_ens is None) or (not self.is_energy_dependent()):
            return prim(phases)*self.norms()[index]
        if weights is None:
            weights = np.ones_like(log10_ens)
        edges = np.linspace(log10_ens.min(),log10_ens.max(),bins+1)
        w = np.histogram(log10_ens,weights=weights,bins=edges)
        rvals = np.zeros_like(phases)
        for weight,en in zip(w[0],(edges[:-1]+edges[1:])/2):
            rvals += weight*prim(phases,en)*self.norms(en)[index]
        rvals /= w[0].sum()
        return rvals


def get_gauss2(pulse_frac=1,x1=0.1,x2=0.55,ratio=1.5,width1=0.01,width2=0.02,lorentzian=False,bridge_frac=0,skew=False):
    """Return a two-gaussian template.  Convenience function."""
    n1,n2 = np.asarray([ratio,1.])*(1-bridge_frac)*(pulse_frac/(1.+ratio))
    if skew:
        prim = LCLorentzian2 if lorentzian else LCGaussian2
        p1,p2 = [width1,width1*(1+skew),x1],[width2*(1+skew),width2,x2]
    else:
        if lorentzian:
            prim = LCLorentzian; width1 *= (2*np.pi); width2 *= (2*np.pi)
        else:
            prim = LCGaussian
        p1,p2 = [width1,x1],[width2,x2]
    if bridge_frac > 0:
        nb = bridge_frac*pulse_frac
        b = LCGaussian(p=[0.1,(x2+x1)/2])
        return LCTemplate([prim(p=p1),b,prim(p=p2)],[n1,nb,n2])
    return LCTemplate([prim(p=p1),prim(p=p2)],[n1,n2])

def get_gauss1(pulse_frac=1,x1=0.5,width1=0.01):
    """Return a one-gaussian template.  Convenience function."""
    return LCTemplate([LCGaussian(p=[width1,x1])],[pulse_frac])

def get_2pb(pulse_frac=0.9,lorentzian=False):
    """ Convenience function to get a 2 Lorentzian + Gaussian bridge template."""
    prim = LCLorentzian if lorentzian else LCGaussian
    p1 = prim(p=[0.03,0.1])
    b = LCGaussian(p=[0.15,0.3])
    p2 = prim(p=[0.03,0.55])
    return LCTemplate(primitives=[p1,b,p2],norms=[0.3*pulse_frac,0.4*pulse_frac,0.3*pulse_frac])

def make_twoside_gaussian(one_side_gaussian):
    """ Make a two-sided gaussian with the same initial shape as the
        input one-sided gaussian."""
    g2 = LCGaussian2() 
    g1 = one_side_gaussian
    g2.p[0] = g2.p[1]= g1.p[0]
    g2.p[-1] = g1.p[-1]
    return g2

class GaussianPrior(object):

    def __init__(self,locations,widths,mod,mask=None):
        self.x0 = np.where(mod,np.mod(locations,1),locations)
        self.s0 = np.asarray(widths)*2**0.5
        self.mod = np.asarray(mod)
        if mask is None:
            self.mask = np.asarray([True]*len(locations))
        else: 
            self.mask = np.asarray(mask)
            self.x0 = self.x0[self.mask]
            self.s0 = self.s0[self.mask]
            self.mod = self.mod[self.mask]

    def __len__(self):
        """ Return number of parameters with a prior."""
        return self.mask.sum()

    def __call__(self,parameters):
        if not np.any(self.mask): return 0
        parameters = parameters[self.mask]
        parameters = np.where(self.mod,np.mod(parameters,1),parameters) 
        return np.sum(((parameters-self.x0)/self.s0)**2)

    def gradient(self,parameters):
        if not np.any(self.mask):
            return np.zeros_like(parameters)
        parameters = parameters[self.mask]
        parameters = np.where(self.mod,np.mod(parameters,1),parameters)
        rvals = np.zeros(len(self.mask))
        rvals[self.mask] = 2*(parameters-self.x0)/self.s0**2
        return rvals

def prim_io(template):
    """ Read files and build LCPrimitives. """

    def read_gaussian(toks):
        primitives = []
        norms = []
        for i,tok in enumerate(toks):
            if tok[0].startswith('phas'):
                g = LCGaussian()
                g.p[-1] = float(tok[2])
                g.errors[-1] = float(tok[4])
                primitives += [g]
            elif tok[0].startswith('fwhm'):
                g = primitives[-1]
                g.p[0] = float(tok[2])/2.3548200450309493      # kluge for now
                g.errors[0] = float(tok[4])/2.3548200450309493
            elif tok[0].startswith('ampl'):
                norms.append(float(tok[2]))
        return primitives,norms

    toks = [line.strip().split() for line in file(template) if len(line.strip()) > 0]
    if 'gauss' in toks[0]:     return read_gaussian(toks[1:])
    elif 'kernel' in toks[0]:  return [LCKernelDensity(input_file=toks[1:])],None
    elif 'fourier' in toks[0]: return [LCEmpiricalFourier(input_file=toks[1:])],None
    raise ValueError,'Template format not recognized!'

