"""
setup and run pointlike all-sky analysis for subset of ROIs

$Header$
"""
import os, sys, logging
from collections import OrderedDict

import numpy as np

### Set variables corresponding to the environment
# these can be overridden by setting environment variables
# note that all are treated as strings
# if None, must be set

defaults=OrderedDict([
	('HOSTNAME', '?'),
	('PIPELINE_STREAMPATH', '-1'),
	('PIPELINE_STREAM', '-1'),

    ('POINTLIKE_DIR','.'),
    ('SKYMODEL_SUBDIR','?'),
    ('stage', '?'),
    ('begin_roi','0'), # defaults for test.
    ('end_roi', '1'),
    ])
    
def main(args=None):
    print '\npointlike skymodel configuration'
    for key,default_value in defaults.items():
        item = (key, os.environ.get(key, default_value))
        exec('%s="%s"'%item)
        print '\t%-20s: %s' % item

    if args is not None and args.test:
        print 'test mode, quitting'
        return 
    # make sure that matplotlib conif is ok
    #os.environ['MPLCONFIGDIR'] = POINTLIKE_DIR+'./matplotlib
	
    np.seterr(invalid='warn', divide='warn')

    streamlogdir = os.path.join(POINTLIKE_DIR,SKYMODEL_SUBDIR,'streamlogs')
    streamlogfile=os.path.join(streamlogdir,'stream%s.%04d.log' % ( PIPELINE_STREAMPATH.split('.')[0], int(PIPELINE_STREAM)) )
    if not os.path.exists(streamlogdir): os.mkdir(streamlogdir)
    print 'Logging execution progress to %s' % streamlogfile
    if os.path.exists(streamlogfile):
       print 'found existing steam log file:%s' % streamlogfile
       with open(streamlogfile) as f:
            lines= f.read().split('\n')
            lastline = lines[-1] if len(lines[-1])>0 else lines[-2]
            if 'Start roi' in lastline: 
               begin_roi = lastline.split()[-1]
               print 'Resuming execution with roi at %s' %begin_roi
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, filename=streamlogfile   )

    ### set up object with skymodel and data
    tzero = tnow = logging.time.time()
    logging.info('Start setup: rois %s-%s on host %s' % (int(begin_roi), int(end_roi)-1, 
        os.environ.get('HOSTNAME','unknown')))

    from uw.like2.pipeline import pipe
    mstage = stage
    stage=stage.split(':')[0] # allows multiple stages, separated by colons
    if stage=='create':
        update = pipe.Create(POINTLIKE_DIR, SKYMODEL_SUBDIR,)
    elif stage=='update_full':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, dampen=1.0, sedfig_dir=None, )
    elif stage=='update':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, dampen=0.5, sedfig_dir=None, )
    elif stage=='update_beta': # do an update, freeing/freezing beta when appropriate
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, dampen=1.0, sedfig_dir=None, fix_beta=True)
    elif stage=='update_pivot': # do an update, modifying pivot energy when appropriate
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, dampen=1.0, sedfig_dir=None, repivot=True)
    elif stage=='finish':
        update = pipe.Finish(POINTLIKE_DIR, SKYMODEL_SUBDIR,)
    elif stage=='tables':
        update = pipe.Tables(POINTLIKE_DIR, SKYMODEL_SUBDIR)
    elif stage=='sedinfo':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, 
            processor='processor.full_sed_processor', sedfig_dir='"sedfig"',)
    elif stage=='diffuse':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, 
            processor='processor.roi_refit_processor')
    elif stage=='isodiffuse':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, 
            processor='processor.iso_refit_processor')
    elif stage=='limb':
        update = pipe.Update(POINTLIKE_DIR, SKYMODEL_SUBDIR, 
            processor='processor.limb_processor')
    elif stage=='fluxcorr':     update = pipe.Update( processor='processor.flux_correlations')
    elif stage=='fluxcorriso':  update = pipe.Update( processor='processor.flux_correlations(diffuse="iso", fluxcorr="fluxicorrso")')
    elif stage=='pulsar_table':
        update = pipe.PulsarLimitTables(POINTLIKE_DIR, SKYMODEL_SUBDIR) 
    else:
        raise Exception('stage "%s" not recognized' % stage)

    g = update.g()
    tprev, tnow= tnow, logging.time.time()
    logging.info('Finish: elapsed= %.1f (total %.1f)' % ( tnow-tprev, tnow-tzero ))

    ### process eash ROI


    for s in range(int(begin_roi), int(end_roi)):
        logging.info('Start roi %d' % s )
        g(s)
        tprev, tnow= tnow, logging.time.time()
        logging.info('Finish: elapsed= %.1f (total %.1f)' % ( tnow-tprev, tnow-tzero ))
        sys.stdout.flush()

if __name__=='__main__':
    main()