"""
Limb refit

$Header$

"""

import os, pickle
import numpy as np
import pandas as pd

from skymaps import SkyDir
from . import limb
from .analysis_base import FloatFormat

class LimbRefit(limb.Limb):
    """Limb normalization refit
    <p>Results of a special pipeline run to allow only limb normalization to vary
    %(table)s
    """

    def setup(self, **kw):
        self.plotfolder = 'limb_refit'
        self.source_name='limb'
        self.title='Limb refit'
        files, pickles = self.load_pickles('limb')
        rdict = dict()
        for f,p in zip(files,pickles):
            name = os.path.split(f)[-1][:9]
            front, back = p['model'].parameters if 'model' in p else (np.nan, np.nan)
            if 'model' not in p: p['model']= None
            ra, dec = p['ra'], p['dec']
            skydir = SkyDir(ra,dec)
            glat,glon = skydir.b(), skydir.l()
            if glon>180: glon-=360.
            rdict[name] = dict(ra=ra, dec=dec, glat=glat, glon=glon,skydir=skydir, front=front, back=back)
        self.df = pd.DataFrame(rdict).transpose()
        self.fpar = self.df.front
        self.bpar = self.df.back
        
    def all_plots(self):
        self.table = pd.DataFrame([self.df.front, self.df.back, ], 
                index=['front', 'back']).T.describe().to_html(float_format=FloatFormat(2))
        self.runfigures([self.flux_vs_dec], ['limb_fit_norm_vs_dec'] )