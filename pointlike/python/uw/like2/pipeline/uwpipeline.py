"""
task UWpipeline Interface to the ISOC PipelineII

$Header$
"""
import os, argparse,  datetime
import numpy as np
from uw.like2 import (process, tools, )
from uw.like2.pipeline import (check_data, pipeline_job, check_converge, stream)
from uw.like2.analyze import app


# Instances of these classes are in the procnames dictionary below. They must implement a main function which will
# by run by the Proc
class StartStream(object):
    """ setup, start a stream """
    def main(self, args):
        ps  = stream.PipelineStream()
        for stage in args.stage:
            # note set job_list to the name of a local file in the pointlike folder -- needs better encapsulation
            job_list = args.job_list
            if job_list is None or job_list=='None':
                job_list = stagenames[stage]['job_list']
            ps(stage, job_list, test=args.test)
            
class Summary(object):
    """ runs a sumamry job, via uw.like2.analyze.app"""
    def get_stage(self, args):
        stagelist = args.stage[0] 
        t = stagelist.split(':',1)
        if len(t)==2:
            stage, nextstage = t 
        else: stage,nextstage = t[0], None
        return stage
    def main(self, args):
        stage = self.get_stage(args)
        kw = stagenames[stage].get('sum', None)
        if kw is not None:
            app.main(kw.split())
            
class JobProc(Summary):
    """ process args for running pipeline jobs"""
    def main(self, args):
        stage = self.get_stage(args)
        proc, jobargs = stagenames[stage].setup()
        if args.rois!='':
            print '-->passing roi list:', args.rois
            jobargs['roi_list']=args.rois
        print '--> starting pipeline job: running class %s with args %s' % (proc, jobargs)
        pipeline_job.main(proc, **jobargs)
  
class CheckJobs(Summary):
    """ process args for the check_jobs step"""
    def main(self, args):
        from uw.like2.pub import healpix_map
        stage = self.get_stage(args)
        # do something instead
        check_converge.main(args)

class CheckData(Summary):
    def main(self, args):
        stage = self.get_stage(args)
        if os.path.exists('failed_rois.txt'):
           os.remove('failed_rois.txt')
           print 'Removed file with failed rois'
        
        check_data.main(args)
 
class Proc(dict):
    def __init__(self, run, help='', **kwargs):
        """ run: class or module -- must have main function """
        super(Proc, self).__init__(self,  help=help, **kwargs)
        self.run = run
        self['help']=help

    def __call__(self, args):
        self.run.main(args)
 
procnames = dict(
    # proc names (except for start) are generated by the UWpipeline task as stream executes
    # start actually launches a stream
    start      = Proc(StartStream(), help='start a stream: assumed if no proc is specified'),
    check_data = Proc(CheckData(),   help='check that required data files are present'),
    job        = Proc(JobProc(),     help='run a parallel pipeline job'),
    job_proc   = Proc(JobProc(),     help='run a parallel pipeline job'),
    check_jobs = Proc(CheckJobs(),   help='check for convergence, combine results, possibly submit new stream'),
    summary_plots= Proc(Summary(),   help='Generate summary plots, depending on stage name'),
    )
proc_help = '\nproc names\n\t' \
    +'\n\t'.join(['%-15s: %s' % (key, procnames[key]['help'])  for key in sorted(procnames.keys())])
    
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
    # list is partly recognized by check_converge.py, TODO to incoprorate it here, especially the part that may start a new stream
    create      =  StageBatchJob( dict(update_positions_flag=True),     sum='environment menu counts',  help='Create a new skymodel, follow with update_full',),
    update_full =  StageBatchJob( dict(),     sum='config counts',            help='refit, full update' ),
    update      =  StageBatchJob( dict( dampen=0.5,), sum='config counts',    help='refit, half update' ),
    update_beta =  StageBatchJob( dict( betafix_flag=True),  sum='sourceinfo',help='check beta', ),
    update_pivot=  StageBatchJob( dict( repivot_flag=True),  sum='sourceinfo',help='update pivot', ), 
    update_only =  StageBatchJob( dict(),                   sum='config counts sourceinfo', help='update, no additional stage', ), 
    finish      =  StageBatchJob( dict(finish=True),     sum='sourceinfo localization associations', help='localize, associations, sedfigs', ),
    residuals   =  StageBatchJob( dict(residual_flag=True), sum='residuals',  help='generate residual tables for all sources', ),
    counts      =  StageBatchJob( dict(counts_dir='counts_dir', dampen=0, outdir='.'), sum='counts',  help='generate counts info, plots', ), 
    tables      =  StageBatchJob( dict(tables_flag=True, dampen=0), sum='hptables', job_list='$POINTLIKE_DIR/infrastructure/joblist8.txt', help='Create tsmap and kde maps'),
    seedcheck   =  StageBatchJob( dict(seed_flag=True, dampen=0), sum='seedcheck', help='Check seeds'),
    )
disabled="""
    sedinfo     =  Stage(pipe.Update, dict( processor='processor.full_sed_processor',sedfig_dir='"sedfig"',), sum='frontback',
                            help='process SED information' ),
    galspectra  =  Stage(pipe.Update, dict( processor='processor.roi_refit_processor'), sum='galacticspectra', help='Refit the galactic component' ),
    isospectra  =  Stage(pipe.Update, dict( processor='processor.iso_refit_processor'), sum='isotropicspectra', help='Refit the isotropic component'),
    limb        =  Stage(pipe.Update, dict( processor='processor.limb_processor'),     sum='limbrefit', help='Refit the limb component, usually fixed' ),
    sunmoon     =  Stage(pipe.Update, dict( processor='processor.sunmoon_processor'), sum='sunmoonrefit', help='Refit the SunMoon component, usually fixed' ),
    fluxcorr    =  Stage(pipe.Update, dict( processor='processor.flux_correlations'), sum='fluxcorr', ),
    fluxcorrgal =  Stage(pipe.Update, dict( processor='processor.flux_correlations'), sum='flxcorriso', ),
    fluxcorriso =  Stage(pipe.Update, dict( processor='processor.flux_correlations(diffuse="iso*", fluxcorr="fluxcorriso")'), ),
    pulsar_table=  Stage(pipe.PulsarLimitTables,),
    localize    =  Stage(pipe.Update, dict( processor='processor.localize(emin=1000.)'), help='localize with energy cut' ),
    seedcheck   =  Stage(pipe.Finish, dict( processor='processor.check_seeds(prefix="SEED")',auxcat="seeds.txt"), sum='seedcheck',
                                                                       help='Evaluate a set of seeds: fit, localize with position update, fit again'),
    seedcheck_MRF =  Stage(pipe.Finish, dict( processor='processor.check_seeds(prefix="MRF")', auxcat="4years_SeedSources-MRF.txt"), help='refit MRF seeds'),
    seedcheck_PGW =  Stage(pipe.Finish, dict( processor='processor.check_seeds(prefix="PGW")', auxcat="4years_SeedSources-PGW.txt"), help='refit PGW seeds'),
    pseedcheck  =  Stage(pipe.Finish, dict( processor='processor.check_seeds(prefix="PSEED")',auxcat="pseeds.txt"), help='refit pulsar seeds'),
    fglcheck    =  Stage(pipe.Finish, dict( processor='processor.check_seeds(prefix="2FGL")',auxcat="2fgl_lost.csv"), help='check 2FGL'),
    pulsar_detection=Stage(pipe.PulsarDetection, job_list='joblist8.txt', sum='pts', help='Create ts tables for pulsar detection'),
    gtlike_check=  Stage(pipe.Finish, dict(processor='processor.gtlike_compare()',), sum='gtlikecomparison', help='Compare with gtlike analysis of same sources'),
    uw_compare =  Stage(pipe.Finish, dict(processor='processor.UW_compare(other="uw26")',), sum='uw_comparison', help='Compare with another UW model'),
    tsmap_fail =  Stage(pipe.Update, dict(processor='processor.localize()',), sum='localization', help='tsmap_fail'),
    covariance =  Stage(pipe.Finish, dict(processor='processor.covariance',),  help='covariance matrices'),
    diffuse_info= Stage(pipe.Update, dict(processor='processor.diffuse_info',), help='extract diffuse information'),
""" 
keys = stagenames.keys()
stage_help = '\nstage name, or sequential stages separated by ":" names are\n\t' \
    +  '\n\t'.join(['%-15s: %s' % (key,stagenames[key]['help'])  for key in sorted(stagenames.keys())])

def find_script_folder(cwd):
    """ look for folder with scripts: expect to be in folder containing skymodels or scripts
    cwd : string, current folder
        """
    m = cwd.find('skymodels')
    if m<0:
        print 'WARNING: did not find "skymodels" in path to cwd, which is %s' %cwd
        script_folder=cwd
    else: script_folder=cwd[:m]
    if not os.path.exists(os.path.join(script_folder, 'configure.sh')):
        # try scripts folder
        test = os.path.join(script_folder, 'scripts')
        if os.path.exists(test):
            if not os.path.exists(os.path.join(test, 'configure.sh')):
                raise Exception('Script "configure.sh" not  found in %s or %s' % (script_folder, test) )
            script_folder = test
        else:
            raise Exception('Script "configure.sh" not  found in %s ' % (script_folder,) )
    return script_folder  
  
def check_environment(args):
    if 'SKYMODEL_SUBDIR' not in os.environ:
        os.environ['SKYMODEL_SUBDIR'] = os.getcwd()
    else:
        skymodel = os.environ['SKYMODEL_SUBDIR']
        print 'skymodel:' , skymodel
        assert os.path.exists(skymodel), 'Bad path for skymodel folder: %s' %skymodel
        os.chdir(skymodel)
    cwd = os.getcwd()
    assert os.path.exists('config.txt'), 'expect this folder (%s) to have a file config.txt'%cwd
    
    if args.scripts is None:
        script_folder = find_script_folder(cwd)
    else:
        if not os.path.exists(args.scripts) :
            raise Exception( 'SCRIPT folder %s not found' % args.scripts) 
        if not os.path.exists(os.path.join(args.scripts, 'configure.sh')):
            raise Exception('File "configure.sh" not found in folder %s' % args.scripts)
        script_folder = args.scripts
    
    if args.stage[0] is not None :
        os.environ['stage']=args.stage[0]

    # add these to the Namespace object 
    args.__dict__.update(skymodel=cwd, pointlike_dir=script_folder, script_folder=script_folder)

def check_names(stage, proc):
    if len(stage)==0:
        if proc is  None:
            raise Exception('No proc or stage argement specified')
        if proc not in procnames:
            raise Exception('proc name "%s" not in list %s' % (proc, procnames,keys()))
        return
    if stage[0] is None: 
        raise Exception('no stage specified')
    for s in stage:
        for t in s.split(':'):
            if t not in keys:
                raise Exception('stage "%s" not recognized: expect one of %s' %(t, sorted(keys)))

def main( args ):
    check_environment(args)
    check_names(args.stage, args.proc)
    proc = args.proc
    #tee = tools.OutputTee('summary_log.txt')
    print '\n'+ str(datetime.datetime.today())[:16]
    print '--> %s for %s'%(proc, args.stage)
    if proc not in procnames:
        print 'proc name "%s" not recognized: expect one of %s' % (proc, sorted(procnames))
        return
    try:
        procnames[proc](args)
    except Exception, msg:
        print 'Exception trying to execute procnames[%s](%s):\n\t%s' % ( proc,args, msg)
        raise
    #tee.close()

if __name__=='__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description=""" start a UWpipeline stream, or run a UWpipeline proc; \n
    """+stage_help+proc_help+"""
    \nExamples: 
        uwpipeline create
        uwpipeline finish -p summary_plots
    """)
    parser.add_argument('stage', nargs='*', default=[os.environ.get('stage', None)], help='stage name, default "%(default)s"')
    parser.add_argument('-p', '--proc', default=os.environ.get('PIPELINE_PROCESS', 'start'), 
            help='proc name,  default: "%(default)s"')
    parser.add_argument('--job_list', default=os.environ.get('job_list', None), help='file used to allocate jobs, default "%(default)s"')
    parser.add_argument('--scripts', default=None,    help='script folder for batch, must be writeable default %(default)s')
    parser.add_argument('--rois', default='', help='allow setting of list for special job'),
    parser.add_argument('--stream', default=os.environ.get('PIPELINE_STREAM', -1), help='pipeline stream number, default %(default)s')
    parser.add_argument('--test', action='store_true', help='Do not run' )
    #parser.add_argument('--processor',  help='specify the processor' )
    args = parser.parse_args()
    main(args)
    
