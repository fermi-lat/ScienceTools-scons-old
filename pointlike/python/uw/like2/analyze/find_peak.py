"""
Analysis code to use grids of TSmap values to locate peaks, an alternative
$Header$

"""
from ..pipeline import diagnostic_plots 
from uw.utilities import makepivot 
import os, glob
import numpy as np
import pandas as pd
import pylab as plt

from skymaps import SkyImage, SkyDir

class PeakFinder(object):

    def __init__(self, filename):
        t =os.path.split(os.path.splitext(filename)[0])[-1].split('_')
        self.sourcename= ' '.join(t[:-1]).replace('p', '+')
        self.df = df = SkyImage(filename)
        wcs = df.projector()
        self.tsmap = np.array(df.image())
        nx,ny = df.naxis1(), df.naxis2()
        ix = np.array([ i % nx for i in range(nx*ny)])
        iy = np.array([ i //nx for i in range(nx*ny)])
        vals = np.exp(-0.5*self.tsmap**2) # convert to likelihood from TS
        norm = 1./sum(vals)
        self.peak_fract = norm*vals.max()
        t = [sum(u*vals)*norm for u in  ix,iy, ix**2, ix*iy, iy**2]
        self.T = np.matrix((t[0],t[1]))
        ra,dec = wcs.pix2sph(t[0], t[1])
        self.peak = SkyDir(ra,dec)
        self.scale = wcs.pix2sph(t[0], t[1]+1)[1] -dec
        self.size = nx*self.scale
        # variance in degrees
        self.variance = self.scale**2*(np.matrix(((t[2], t[3]),(t[3], t[4]))) - self.T.T* self.T)
        rac,decc = wcs.pix2sph(nx/2.0, ny/2.0)
        self.offset = np.degrees(self.peak.difference(SkyDir(rac,decc)))
        
    def ellipse(self):
        # add effects of binsize
        var  = self.variance+ np.matrix(np.diag([1,1]))*(self.scale/3)**2
        t,v =np.linalg.eigh(var)
        ang =np.degrees(np.arcsin(np.array(v)[0][0])) #guess. Needs adjustment depending on which is largest
        return t[0],t[1],ang


class SourceList(list):

    def __init__(self, path='tsmap_fail/*.fits'):
        ff = sorted(glob.glob(path))
        print 'found %d files using glob pattern "%s"'  % (len(ff), path)
        for f in ff:
            try:
                q = PeakFinder(f)
            except Exception, msg:
                print 'Failed to load image %s' %f
                continue
            e1,e2, ang = q.ellipse()
            a2 = max(e1,e2)
            b2 = min(e1,e2)
            b2=max(b2,0)
            if e1<e2: 
                ang=90.+ang
                if ang>90: ang-=180
            self.append(dict(name=q.sourcename, sdir=q.peak, 
                ellipse=q.ellipse(), size=q.size,
                ax=np.sqrt(a2), bx=np.sqrt(b2), angx=ang,
                peak_fract = q.peak_fract,
                offset=q.offset,
                tsmap = q.tsmap, )
                )
                
    def __call__(self):
        return pd.DataFrame(self, index=[s['name'] for s in self])

class FindPeak(diagnostic_plots.SourceInfo):
    """Analyze a set of FITS images of TS maps, using <a href="http://en.wikipedia.org/wiki/Moment_(mathematics)">moments</a> to estimate positions of peak and extent.
    <p>The images were generated by the "finish" stage of all-sky into a folder "tsmap_fail". Both smoothed pdf and raw FITS files were created for each one. 
    The FITS can be displayed itself of course. This code uses it to extract the values and positions of the 15x15 image. Each cell contains the square root of the 
    TS, relative to the peak, for a the source to be located there. The associated weight for the moment analysis is the associated probablitly, exp(-TS/2). 
    """
    
    def setup(self, path='tsmap_fail/*.fits', **kw):
        super(FindPeak, self).setup(**kw)

        self.plotfolder='peak_finder'
        
        ff = sorted(glob.glob(path))
        print 'found %d files using glob pattern "%s"'  % (len(ff), path)
        slist = []
        for f in ff:
            try:
                q = PeakFinder(f)
            except Exception, msg:
                print 'Failed to load image %s: "%s"' % (f,msg)
                continue
            e1,e2, ang = q.ellipse()
            a2 = max(e1,e2)
            b2 = min(e1,e2)
            b2=max(b2,0)
            if e1<e2: 
                ang=90.+ang
                if ang>90: ang-=180
            slist.append(dict(name=q.sourcename, sdir=q.peak, 
                ellipse=q.ellipse(), size=q.size,
                ax=np.sqrt(a2), bx=np.sqrt(b2), angx=ang,
                peak_fract = q.peak_fract,
                offset=q.offset,
                tsmap = q.tsmap, )
                )   
        self.xdf=pd.DataFrame(slist, index=[s['name'] for s in slist])
        self.dfs = self.xdf['ax bx angx offset size peak_fract'.split()]
        self.dfs.index.name='name'
        for x in 'ts a b ang locqual delta_ts flags roiname'.split():
            self.dfs[x] = self.df[x]
        self.dfs[self.dfs.flags>7].to_csv('flagged_localizations.csv')
        print 'wrote file %s with TSmap moment analysis' % 'flagged_localizations.csv'
    
    def make_collection(self):
        self.collection_html=''
        try:
            t = makepivot.MakeCollection('flagged localizations %s'%self.skymodel, 'tsmap_fail', 'flagged_localizations.csv', 
                refresh=True) 
            makepivot.set_format(t.cId)
            self.collection_html="""
                <p>The images and associated values can be examined with a 
                <a href="http://deeptalk.phys.washington.edu/PivotWeb/SLViewer.html?cID=%d">Pivot browser</a>,
                which requires Silverlight."""  % t.cId
        except Exception, msg: 
            print "**** Failed to make pivot table: %s" % msg
        return None

    
    def peakfit_comparison(self):
        """Comparison of values from moment analysis with peak fit
        This shows a comparison the major axis size of the moment analysis with the peak-finding algorithm.
        The "peak-like" subset are well-centerer sources, with the maximum bin having between 20 and 80 percent of the
        total weight.
        """ 
        dfs = self.dfs
        cut =(dfs.offset<0.13) * (dfs.peak_fract>0.2) * (dfs.peak_fract<0.8) 
        amax=0.3
        fig, ax = plt.subplots(figsize=(5,5))
        ax.plot(dfs.a.clip(0,amax), dfs.ax.clip(0,amax), '.')
        ax.plot(dfs.a[cut].clip(0,amax), dfs.ax[cut].clip(0,0.5), 'or', label='peak-like')
        ax.plot([0,amax], [0.,amax], '--k')
        ax.legend(loc='upper left')
        plt.setp(ax, xlim=(0,amax+0.01), ylim=(0,amax+0.01), xlabel='fit size', ylabel='moment size')
        return fig
    
    def plots(self):
        """Plots of properties of the moment analysis
        The values shown are:
        <ol><li>peak fraction: fraction of the total weight for the largest bin. This is a check on the scale.
            Small means a uniform distribution, large means scale is too large </li>
            <li>offset:  Distance from center to peak </li>
            <li>major: Size of major axis (1 sigma)</li>
            <li>minor/major: Ratio of minor to major axis size</li>
            <li>size: Size of image. The analysis that generated these images used the peak fitting analysis to set 
            the scale, but limited to 2 degrees.</li>
            <li>locqual : The peak-finding localization quality. This being too large is the primary reason these sources
            were selected. </li>
         </ol>   
         %(collection_html)s
        """
        self.make_collection()
        fig, axx = plt.subplots(2,3, figsize=(10,8))
        plt.subplots_adjust(hspace=0.3, wspace=0.3)
        dfs = self.dfs
        goodfrac=dfs.peak_fract<0.5
        for ix, ax in enumerate(axx.flatten()):
            if ix==0:                       
                ax.hist(dfs.peak_fract, np.linspace(0,1,26))
                plt.setp(ax, xlabel='peak fraction')
            elif ix==1:
                ax.hist(dfs.offset, np.linspace(0,1,26))
                ax.hist(dfs.offset[goodfrac], np.linspace(0,1,26))
                plt.setp(ax, xlabel='offset')
            elif ix==2:
                ax.hist(dfs.ax.clip_upper(0.5), np.linspace(0,0.5,26))
                ax.hist(dfs.ax[goodfrac].clip_upper(0.5), np.linspace(0,0.5,26))
                plt.setp(ax, xlabel='major')
            elif ix==3:
                ax.hist(dfs.bx/dfs.ax, np.linspace(0,1,26))
                ax.hist((dfs.bx/dfs.ax)[goodfrac], np.linspace(0,1,26))
                plt.setp(ax, xlabel='minor/major')
            elif ix==4:
                ax.hist(dfs.size, np.linspace(0,2,26))
                ax.hist(dfs.size[goodfrac], np.linspace(0,2,26))
                plt.setp(ax, xlabel='size')
            elif ix==5:
                ax.hist(dfs.locqual.clip_upper(8), np.linspace(0,8))
                plt.setp(ax, xlabel='locqual')
            def all_plots(self):
                self.runfigures([ self.peakfit_comparison,])
        return fig
        
    def all_plots(self):
        self.runfigures([self.plots, self.peakfit_comparison,])
  
diagnostic_plots.opts.update(findpeak= (FindPeak,)) # this may not be useful
  
if __name__=='__main__':
    #FindPeak().all_plots()
    diagnostic_plots.main('findpeak')
    
