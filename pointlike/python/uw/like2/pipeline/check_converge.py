"""
Run after a successful UWpipeline/job_task

Summarize the execution, 
mostly zipping the files generated by the multiple jobs and submitting follow-up streams
diagnostic plots are now done by the summary task


$Header$
"""
import os, sys, glob, zipfile, logging, datetime, argparse
import numpy as np
import pandas as pd

from uw.like2.pipeline import pipe, processor


def streamInfo( stream, path='.'):
    streamlogs=sorted(glob.glob(os.path.join(path,'streamlogs','stream%s.*.log'%stream)))
    if len(streamlogs)==0:
	print 'Did not find stream %d logfiles'% stream
	return
    substream = [ int(f.split('.')[-2]) for f in streamlogs]
    print '\t found %d streamlog files...' %(len(streamlogs),), 
    etimes =np.array([ float(open(f).read().split('\n')[-2].split()[-1][:-1]) for f in streamlogs])
    print '\texecution times: mean=%.1f, max=%.1f'% (etimes.mean(), etimes.max())
    times = pd.DataFrame(dict(etimes=etimes), index=pd.Index(substream, name='substream'))#,name='stream%d'%stream)
    bad = times[times.etimes>2*times.etimes.mean()]
    if len(bad)>0:
        print '\tsubstreams with times>2*mean:'
        print bad
    return times




def main(args):
    """ 
    """
    pointlike_dir=args.pointlike_dir # = os.environ.get('POINTLIKE_DIR', '.')
    skymodel=args.skymodel # = os.environ.get('SKYMODEL_SUBDIR', sys.argv[1] )
    stream = args.stream 
    stagelist = args.stage
    if hasattr(stagelist, '__iter__'): stagelist=stagelist[0] #handle local or from uwpipeline.py
   
    absskymodel = os.path.join(pointlike_dir, skymodel)

    def make_zip(fname,  ext='pickle'):
        ff = glob.glob(os.path.join(absskymodel, fname, '*.'+ext))
        if len(ff)==0:
            print 'no files found to zip in folder %s' %fname
            return
        print 'found %d *.%s in folder %s ...' % ( len(ff),ext, fname,) ,
        with zipfile.ZipFile(os.path.join(absskymodel, fname+'.zip'), 'w') as z:
            for filename in ff:
                z.write( filename, os.path.join(fname,os.path.split(filename)[-1]))
        print ' zipped into file %s.zip' %fname
        
    def create_stream(newstage):
        cmd = 'cd %s;  /afs/slac/g/glast/ground/bin/pipeline  createStream -D "stage=%s, SKYMODEL_SUBDIR=%s" UWpipeline '\
            %(pointlike_dir, newstage, skymodel)
        if args.test:
            print 'Test mode: would have submitted %s'%cmd
            return
        rc=os.system(cmd)
        if rc==0:
            print '\n----> started new stream with stage %s'% newstage
        else: print '\n***** Failed to create new stream: tried %s'%cmd


    if not args.test:
        tee = processor.OutputTee(os.path.join(absskymodel, 'summary_log.txt'))

    streamInfo(stream, absskymodel)

    os.chdir(absskymodel) # useful for diagnostics below
    current = str(datetime.datetime.today())[:16]
    print '\n%s stage %s stream %s model %s ' % (current, stagelist, stream,  absskymodel)

    t = stagelist.split(':',1)
    if len(t)==2:
        stage, nextstage = t 
    else: stage,nextstage = t[0], None

    if stage.split('_')[0]=='update':
        make_zip('pickle') # always update; latter diagnostic will use it, not the files
        logto = open(os.path.join(absskymodel,'converge.txt'), 'a')
        pipe.check_converge(absskymodel, log=logto)
        r = pipe.roirec(absskymodel)
        q = pipe.check_converge(absskymodel, add_neighbors=False)
        if max(r.niter)<5 and len(q)>1:
            create_stream('update')
        else:
            create_stream('finish')
            
    elif stage=='sedinfo':
        make_zip('sedinfo')
        make_zip('sedfig','png')

    elif stage=='create' or stage=='create_reloc':
        ff = glob.glob(os.path.join(absskymodel, 'pickle', '*.pickle'))
        print 'found %d pickled ROI files' % len(ff)
        
        if nextstage is None:
            create_stream('update_full') # always start an update

    elif stage=='diffuse':
        make_zip('galfit_plots', 'png')
        make_zip('galfits_all')

    elif stage=='isodiffuse':
        make_zip('isofit_plots', 'png')
        make_zip('isofits')

    elif stage=='limb':
        make_zip('limb')

    elif stage=='finish':
        make_zip('pickle')

    elif stage=='tables':
        make_zip('ts_table')
        make_zip('kde_table')
        make_zip('counts_table')
    else: # catch fluxcorr, any others like
        if os.path.exists(stage):
            make_zip(stage)
        else:
            print 'stage %s not recognized for summary'%stage 
    if not args.test:
        if nextstage:
            create_stream(nextstage)
        tee.close()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Run after a set of pipeline jobs, check status, accumulate info')
    parser.add_argument('--stage', default=os.environ.get('stage', '?'), help='the stage indentifier(s)')
    parser.add_argument('--pointlike_dir', default=os.environ.get('POINTLIKE_DIR', '.'),
            help='top level folder with pointlike')
    parser.add_argument('--skymodel', default= os.environ.get('SKYMODEL_SUBDIR', '.'),
            help='folder, from pointlike_dir, to the skymodel. Default $SKYMODEL_SUBDIR, set by pipeline')
    parser.add_argument('--stream', default = os.environ.get('PIPELINE_STREAM', '0'),
            help='stream number')
    parser.add_argument('--test', action='store_true', help='test mode')
    args = parser.parse_args()
    main(args)

