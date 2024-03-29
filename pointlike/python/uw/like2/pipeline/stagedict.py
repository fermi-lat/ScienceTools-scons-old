"""
Define stages

$$
"""
import numpy as np
from uw.like2 import (process, tools, )

    
class Stage(dict):
    def __init__(self, proc, pars={}, job_list='$POINTLIKE_DIR/infrastructure/joblist.txt', help='', **kwargs):
        super(Stage,self).__init__(proc=proc, pars=pars, help=help, **kwargs)
        self['help']=help
        self['job_list']=job_list
    def setup(self):
        return self['proc'], self['pars']

class StageBatchJob(Stage):
    """Stage a batch job
    Note that job_list default is '$POINTLIKE_DIR/joblist.txt', but can be overridden 
    """
    def __init__(self, pars={}, job_list='$POINTLIKE_DIR/infrastructure/joblist.txt', help='', **kwargs):
        super(StageBatchJob,self).__init__(process.BatchJob, pars, job_list, help, **kwargs)
        
stagenames = dict(
    # List of possible stages, with proc to run, parameters for it,  summary string
    # list is recognized by check_converge, which will use next, if it exists, for the fillong
    create      =  StageBatchJob( dict(update_positions_flag=True),     sum='environment menu counts',  help='Create a new skymodel, follow with update_full',),
    update_full =  StageBatchJob( dict(),     sum='config counts',            help='refit, full update' ),
    update      =  StageBatchJob( dict( dampen=0.5,), sum='config counts',    help='refit, half update' ),
    betafix_only=  StageBatchJob( dict( betafix_flag=True),  sum='counts sourceinfo',help='check beta', ),
    betafix     =  StageBatchJob( dict( betafix_flag=True),  sum='counts sourceinfo',help='check beta', ),
    update_pivot=  StageBatchJob( dict( repivot_flag=True),  sum='sourceinfo',help='update pivot', ), 
    update_only =  StageBatchJob( dict(),                   sum='config counts sourceinfo', help='update, no additional stage', ), 
    update_positions
                =  StageBatchJob( dict(update_positions_flag=True, dampen=1.0), sum='sourceinfo', help='update positions and refit', ),
    #update_norms=  StageBatchJob( dict( norms_only=True), sum='menu config counts', help='update that fits the normalization factors only'),
    
    monthlyPGW    =  StageBatchJob( dict( fix_spectra_flag=True), sum='menu config counts', next='addseeds_PGW', help='create a monthly model; followed by adding PGW seeds for that month'),
    monthly     =  StageBatchJob( dict( fix_spectra_flag=True), sum='menu config counts', next='tables', help='create a monthly model; followed by a tsmap'),
    monthlynopgw =  StageBatchJob( dict( fix_spectra_flag=True), sum='menu config counts', next='update_full', help='create a monthly model, no seeds, just update'),
    addseeds    =  StageBatchJob( dict(seed_key=''), next='update_full', sum='config counts', help='start update sequence with seeds'),
    addseeds_pgw=  StageBatchJob( dict(seed_key='pgw'), next='update_full', sum='config counts pgwave', help='start update sequence with PGW seeds'),
    addseeds_PGW=  StageBatchJob( dict(seed_key='PGW'), next='update_full', sum='config counts pgwave', help='start update sequence with new PGW seeds'),
    addseeds_ts =  StageBatchJob( dict(seed_key='ts'), next='update_full', sum='config counts', help='start update sequence with TS map seeds'),
    addseeds_3fhl =  StageBatchJob( dict(seed_key='3FHL'), next='update_full', sum='config counts', help='start update sequence with 3FHL seeds'),
    addseeds_hard =  StageBatchJob( dict(seed_key='hard'), next='update_full', sum='config counts', 
        help='start update sequence with hard source seeds'),
    addseeds_soft =  StageBatchJob( dict(seed_key='soft'), next='update_full', sum='config counts', 
        help='start update sequence with very soft source seeds'),
    addseeds_psr =  StageBatchJob( dict(seed_key='tsp'), next='update_full', sum='config counts', 
        help='start update sequence with pulsar-like seeds'),
    
    #update_seeds=  StageBatchJob( dict(add_seeds_flag=True), sum='config counts', help='start update sequence with new seed soruces'),
    finish      =  StageBatchJob( dict(finish=True),     sum='sourceinfo localization associations', help='localize, associations, sedfigs', ),
    finish_month=  StageBatchJob( dict(finish=True),     sum='transientinfo', help='plots for monthly transients', ),
    residuals   =  StageBatchJob( dict(residual_flag=True), sum='residuals',  help='generate residual tables for all sources', ),
    counts      =  StageBatchJob( dict(counts_dir='counts_dir', dampen=0, outdir='.'), sum='counts',  help='generate counts info, plots', ), 
    tables      =  StageBatchJob( dict(tables_flag=True, dampen=0), next='addseeds_ts', 
        sum='hptables', job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create tsmap and kde maps'),
    tables_tsp  =  StageBatchJob( dict(table_keys=['tsp'], dampen=0),
         job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create pulsar ts map'),
    tables_hard  =  StageBatchJob( dict(table_keys=['hard'], dampen=0),
         job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create hard source TS map'),
    tables_soft  =  StageBatchJob( dict(table_keys=['soft'], dampen=0), next='addseeds_soft',
         job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create hard source TS map'),
    residualmaps = StageBatchJob( dict(table_keys=['rmap'], dampen=0),  job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create residual maps'),
    #xtables     =  StageBatchJob( dict(xtables_flag=True, dampen=0), job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create special tsmap'),
    seedcheck   =  StageBatchJob( dict(seed_key='ts',  dampen=0), sum='seedcheck', help='Check seeds'),
    #seedcheck_tsp= StageBatchJob( dict(seed_key='tsp', dampen=0),  help='Check pulsar seeds'),
    #seedcheck_pgw= StageBatchJob( dict(seed_key='pgw', dampen=0),  sum='seedcheck', help='Check seeds from PGW'),
    special     =  StageBatchJob( dict(special_flag=True), sum='counts', help='Special processing, then updates'),
    special_only=  StageBatchJob( dict(special_flag=True), sum='counts', help='Special processing only'),
    fitdiffuse  =  StageBatchJob( dict(diffuse_flag=True), sum='diffuse_correction',  help='special diffuse fits'),
    tables_mspsens =StageBatchJob( dict(table_keys=['mspsens'], dampen=0, tables_nside=256),
         job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create MSP sensitivity map'), 
    )
keys = stagenames.keys()
help = '\nstage name, or sequential stages separated by "y:" names are\n\t' \
    +  '\n\t'.join(['%-15s: %s' % (key,stagenames[key]['help']) \
        for key in sorted(stagenames.keys())])

