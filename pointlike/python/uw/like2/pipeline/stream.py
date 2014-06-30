"""
manage creating new PipelineII stream

$Header$
"""
import os, datetime
import numpy as np


class PipelineStream(object):
    """ manage starting streams
    Assume that POINTLIKE_DIR is defined, and that current directory is a skymodel
    """
    def __init__(self, fn='summary_log.txt'):
        self.pointlike_dir=os.path.expandvars('$POINTLIKE_DIR')
        self.summary= os.path.join(self.pointlike_dir,fn)
        self.fullskymodel = os.getcwd()
        assert os.path.exists(self.summary), 'File "%s" not found' % self.summary
        assert os.path.exists('config.txt'), 'File config.txt not found in %s' %self.model
        t =self.fullskymodel.split('/')
        self.model = '/'.join(t[t.index('skymodels')+1:])
        with open(self.summary, 'r') as slog:
            lines = slog.read().split('\n')
            last = lines[-1] if lines[-1] != '' else lines[-2] 
            try:
                self.stream_number = int(last.split()[0])
            except:
                print 'failed to interpret stream number from file %s: last=%s' % (self.summary,self.last)
                raise
            
    def __call__(self,  stage, job_list, test=True):
        """Submit a command to the Pipeline to create a stream
        """
        pipeline='/afs/slac/g/glast/ground/bin/pipeline -m PROD createStream --stream %d -D "%s" UWpipeline '

        self.stream_number += 1
        time = str(datetime.datetime.today())[:16]
        line = '%5d  %s %-15s %-10s %s' % (self.stream_number, time, self.model, stage, job_list)
        print line
        with open(self.summary, 'a') as slog:
            slog.write('\n'+line)
        cmd=pipeline % (self.stream_number, 
                "stage=%s, POINTLIKE_DIR=%s, SKYMODEL_SUBDIR=%s, job_list=%s"
                    % (stage, self.pointlike_dir, self.fullskymodel, job_list)
                )
        if not test:
            print '-->' , cmd
            os.system(cmd)
        else:
            print 'Test mode: would have submitted \n\t%s'%cmd