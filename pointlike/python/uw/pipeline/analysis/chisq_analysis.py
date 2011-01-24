"""
Analyze the ROI chi squared distributions
"""
import os, glob, pickle, types
import numpy as np
import pylab as plt
from skymaps import SkyDir

def get_outdir():
    version = int(open('version.txt').read())
    ret = 'uw%02d' % version
    print 'using folder %s' % ret
    return ret
    
def load_count_data(outdir=None):
    if outdir is None:
        outdir=get_outdir()
    pkfiles = glob.glob(os.path.join(outdir,'pickle', '*.pickle'))
    clist = [pickle.load(open(fname)) for fname in np.sort(pkfiles)]
    if len(clist)<1728: print 'warning: missing pickle files? found %d/1726' %len(clist)
    return clist
    
    
class Chisq(object):

    def __init__(self, clist=None, skysel=None):
        """ 
        clist: list of pickled roi 
        skysel : None, or a tuple (function, description)
                the function, of a SkyDir, must return a bool: example
                 skysel=(lambda s: abs(s.b())>10, '|b|.10')
        """
        if clist is None: clist = load_count_data()
        self.obs =[]
        self.gal =[]
        self.iso =[]
        self.src =[]
        self.tot =[]
        self.energies =clist[0]['counts']['energies']
        self.nroi= 0
        self.subset = 'All sky' if skysel is None else skysel[1]
        self.index_array = []
        for index,roi in enumerate(clist):
            glat = roi['skydir'].b()
            if skysel is not None:
                if not skysel[0](roi['skydir']): continue
            self.nroi +=1
            self.index_array.append(index)
            counts=roi['counts']
            models = counts['models']
            self.obs.append( counts['observed'])
            self.gal.append( models[0][1])
            self.iso.append( models[1][1])
            self.src.append( models[2][1])
            self.tot.append( counts['total']) # should be sum of gal,iso,src 
        self.nband = len(self.energies)
        self.which = 1
        print 'loaded %d ROIs (%s) total counts: %d' % (self.nroi, self.subset, np.sum(self.obs))
        self._chisq = self.chisq()
        
    def chisq(self, start=0, stop=None):
        tot = np.array(self.tot)
        obs = np.array(self.obs)
        q = (tot-obs)**2/tot
        if stop is None: stop = self.nband
        sl = slice(start, stop)
        return np.array([np.sum(t[sl]) for t in q])
    
    def hist(self, fignum=2, axes=None, cmax=50, bins=25, **qwargs):
        t = self._chisq.copy()
        t[t>cmax]= cmax
        if axes is None:
            plt.close(fignum)
            fig = plt.figure(fignum)
            axes = fig.gca()
        axes.hist(t, np.linspace(0, cmax, bins+1), label=self.subset, **qwargs); 
        axes.grid()
        axes.legend()
        axes.figure.show()
        
    def __call__(self, j, x=0):
        """
        value of chisquared, adjusting band k by 1+x
        """
        c2 = 0
        corr = np.zeros(self.nband,float)
        corr[j]=x
        for i in range(self.nroi):
            gal,iso,src,obs,tot = self.gal[i], (1+corr)*self.iso[i], self.src[i],self.obs[i],self.tot[i]
            for j in range(self.nband):
                c2 += (gal[j]+iso[j]+src[j]-obs[j])**2/tot[j]
        return c2
        
    def prime(self, j, x):
        """ first and second derivatives with respect to iso[k]
            evaluate after adjusting k'th band by 1+x
        """
        c1=c2 = 0
        corr = np.zeros(self.nband,float)
        corr[j]=x
        # make correction
        for i in range(self.nroi):
            gal,iso,src = self.gal[i], (1+corr)*self.iso[i], self.src[i]
            obs,tot = self.obs[i],self.tot[i]
            t = (gal[j]+iso[j]+src[j]-obs[j])/tot[j]
            w = iso[j] 
            if self.which==0 : w= gal[j]
            elif self.which==2: w = src[j]
            c1+= t*w
            c2+= w**2/tot[j]
        return c1,c2
    
    def estimate(self, j=None):
        """ return estimated value at chi squared minimum"""
        if j is not None:
            c1,c2 = self.prime(j, 0.)
            return -c1/c2, 1/np.sqrt(c2)
        t = np.array([self.prime(j,0) for j in range(self.nband)])
        return -t[:,0]/t[:,1], 1/np.sqrt(t[:,1])
    
    def update(self, infile, outfile=None):
        """ update a diffuse file using these data
        """
        out = open(outfile, 'w') if outfile is not None else None
        corr = map(self.estimate, range(self.nband))
        for line in open(infile):
            if len(line)==0: break
            e, x, dx =np.array(line.split(), float)
            print e, x, dx,
            for i,ep in enumerate(self.energies):
                if np.abs(e-ep)<0.01*ep:
                    #print i, corr[i],
                    x*=(1+corr[i])
                    dx = 0
            print ' %.3e' % x
            if out is not None:
                print >>out, '%10.1f %10.3e %10.3g' % (e, x, dx)
        if out is not None: out.close()

    def plot(self, title=None, axes=None, fignum=1, **kwargs):
        """ make a plot showing the implied corrections for each of the components
        """
        if axes is None:
            plt.close(fignum)
            fig = plt.figure(fignum)
            axes = fig.gca()
        sym = 'ods'
        x = self.energies    
        for i,label in enumerate('galactic isotropic sources'.split()):
            self.which= i
            y, yerr = self.estimate()
            axes.errorbar(x*(1.+0.05*(i-1)), 100*y, yerr= 2.5*100*yerr, fmt=sym[i],  label=label, **kwargs)
        axes.set_xscale('log')
        axes.axhline(0)
        axes.set_xlabel('Energy (Mev)')
        axes.set_ylabel('Fractional deviation (%)')
        axes.set_xlim((100,1e6))
        axes.legend(loc='lower left')
        axes.grid(True)
        if title is not None: axes.set_title(title)
        else: axes.set_title(self.subset)
    
def go(clist=None, fignum=1, title=None, ylim=50):
    """ make multiple plots for Chisq """
    if clist is None: clist = load_count_data()
    plt.close(fignum)
    fig, ax = plt.subplots(2,3, sharex=True,sharey=True, num=fignum, figsize=(14,12))

    subsets = ( None,
        (lambda s: np.abs(s.b())>5 and np.abs(s.b())<40, '|b|>5 and |b|<40'),
        (lambda s: np.abs(s.b())>40, '|b|>40'),
        (lambda s: np.abs(s.b())<5, '|b|<5'),
        (lambda s: np.abs(s.b())<5 and (s.l()<60  or s.l()>300),  'ridge'),
        )

    for axes,subset in zip(ax.flatten(), subsets):
        c2 = Chisq(clist, subset)
        c2.plot(axes=axes, title='', ms=8)
        axes.text( 0.1, 0.9, c2.subset, transform = axes.transAxes)
    ax[0,0].set_ylim((-ylim,ylim))
    for axes in ax.flatten()[len(subsets):]: axes.set_axis_off() #blank unused
    if title is not None:
        fig.suptitle(title, fontsize=14)
    fig.show()
    