#$Id$
def generate(env, **kw):
	if not kw.get('depsOnly',0):
		env.Tool('addLibrary', library = ['st_stream'])

def exists(env):
	return 1
