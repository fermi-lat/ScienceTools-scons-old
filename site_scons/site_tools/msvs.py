#  $Id$
""" Site-specific msvs, from SCons.Tool.msvs

    27 Feb  Get rid of some stuff which I don't think is being used
    
Tool-specific initialization for Microsoft Visual Studio project files.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import base64
import hashlib
import ntpath
import os
import os.path

import re
import string
import sys

import SCons.Builder
import SCons.Node.FS
import SCons.Platform.win32
import SCons.Script.SConscript
import SCons.Util
import SCons.Warnings
from   SCons.Script import *
from   fermidebug import fdebug


#from SCons.Tool.MSCommon import detect_msvs, merge_default_version
if sys.platform == 'win32':
    # for 1.3.0
    from SCons.Tool.MSCommon import msvc_exists, msvc_setup_env_once
    # don't think we need processDefines for our version
    #from SCons.Defaults import processDefines 

##############################################################################
# Below here are the classes and functions for generation of
# DSP/DSW/SLN/VCPROJ files.
##############################################################################

def _hexdigest(s):
    """Return a string as a string of hex characters.
    """
    # NOTE:  This routine is a method in the Python 2.0 interface
    # of the native md5 module, but we want SCons to operate all
    # the way back to at least Python 1.5.2, which doesn't have it.
    h = string.hexdigits
    r = ''
    for c in s:
        i = ord(c)
        r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
    return r

def xmlify(s):
    s = string.replace(s, "&", "&amp;") # do this first
    s = string.replace(s, "'", "&apos;")
    s = string.replace(s, '"', "&quot;")
    return s

external_makefile_guid = '{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}'

def _generateGUID(slnfile, name):
    """This generates a dummy GUID for the sln file to use.  It is
    based on the MD5 signatures of the sln filename plus the name of
    the project.  It basically just needs to be unique, and not
    change with each invocation."""
    m = hashlib.md5()
    # Normalize the slnfile path to a Windows path (\ separators) so
    # the generated file has a consistent GUID even if we generate
    # it on a non-Windows platform.
    m.update(ntpath.normpath(str(slnfile)) + str(name))
    # TODO(1.5)
    #solution = m.hexdigest().upper()
    solution = string.upper(_hexdigest(m.digest()))
    # convert most of the signature to GUID form (discard the rest)
    solution = "{" + solution[:8] + "-" + solution[8:12] + "-" + solution[12:16] + "-" + solution[16:20] + "-" + solution[20:32] + "}"
    return solution

version_re = re.compile(r'(\d+\.\d+)(.*)')

# pattern to find end-of-token .cxx, .cc or .c
cfile_re = re.compile(r'(\.cxx|.cc|.c)( |$)')

# pattern to replace src directory with Studio variant
cfiledir_re = re.compile(r'( |^)(?P<fdir>[^ ]*\\)?(?P<f>[^ \\]+\.obj)')

def msvs_parse_version(s):
    """
    Split a Visual Studio version, which may in fact be something like
    '7.0Exp', into is version number (returned as a float) and trailing
    "suite" portion.
    """
    num, suite = version_re.match(s).groups()
    return float(num), suite

# This is how we re-invoke SCons from inside MSVS Project files.
#     Don't need this
#def getExecScriptMain(env, xml=None):

# The string for the Python executable we tell the Project file to use
# is either sys.executable or, if an external PYTHON_ROOT environment
# variable exists, $(PYTHON)ROOT\\python.exe (generalized a little to
# pluck the actual executable name from sys.executable).
try:
    python_root = os.environ['PYTHON_ROOT']
except KeyError:
    python_executable = sys.executable
else:
    python_executable = os.path.join('$$(PYTHON_ROOT)',
                                     os.path.split(sys.executable)[1])

class Config:
    pass

def splitFully(path):
    dir, base = os.path.split(path)
    if dir and dir != '' and dir != path:
        return splitFully(dir)+[base]
    if base == '':
        return []
    return [base]

def makeHierarchy(sources):
    '''Break a list of files into a hierarchy; for each value, if it is a string,
       then it is a file.  If it is a dictionary, it is a folder.  The string is
       the original path of the file.'''

    hierarchy = {}
    for file in sources:
        path = splitFully(file)
        if len(path):
            dict = hierarchy
            for part in path[:-1]:
                if not dict.has_key(part):
                    dict[part] = {}
                dict = dict[part]
            dict[path[-1]] = file
    return hierarchy

class _DSPGenerator:
    """ Base class for DSP generators """

    srcargs = [
        'srcs',
        'incs',
        'localincs',
        'resources',
        'misc']

    def __init__(self, dspfile, source, env):
        self.dspfile = str(dspfile)
        try:
            get_abspath = dspfile.get_abspath
        except AttributeError:
            self.dspabs = os.path.abspath(dspfile)
        else:
            self.dspabs = get_abspath()

        if not env.has_key('variant'):
            raise SCons.Errors.InternalError, \
                  "You must specify a 'variant' argument (i.e. 'Debug' or " +\
                  "'Release') to create an MSVSProject."
        elif SCons.Util.is_String(env['variant']):
            variants = [env['variant']]
        elif SCons.Util.is_List(env['variant']):
            variants = env['variant']

        if env.has_key('gr_app_src'):
            gr_app_src = env['gr_app_src']
            self.gr_app_src = gr_app_src.replace("#", "..\\..\\")
        else:
            self.gr_app_src = '..\\..\\gr_app\\src'
        if not env.has_key('buildtarget') or env['buildtarget'] == None:
            buildtarget = ['']
        elif SCons.Util.is_String(env['buildtarget']):
            buildtarget = [env['buildtarget']]
        elif SCons.Util.is_List(env['buildtarget']):
            if len(env['buildtarget']) != len(variants):
                raise SCons.Errors.InternalError, \
                    "Sizes of 'buildtarget' and 'variant' lists must be the same."
            buildtarget = []
            for bt in env['buildtarget']:
                if SCons.Util.is_String(bt):
                    buildtarget.append(bt)
                else:
                    buildtarget.append(bt.get_abspath())
        else:
            buildtarget = [env['buildtarget'].get_abspath()]
        if len(buildtarget) == 1:
            bt = buildtarget[0]
            buildtarget = []
            for _ in variants:
                buildtarget.append(bt)

        if not env.has_key('outdir') or env['outdir'] == None:
            outdir = ['']
        elif SCons.Util.is_String(env['outdir']):
            outdir = [env['outdir']]
        elif SCons.Util.is_List(env['outdir']):
            if len(env['outdir']) != len(variants):
                raise SCons.Errors.InternalError, \
                    "Sizes of 'outdir' and 'variant' lists must be the same."
            outdir = []
            for s in env['outdir']:
                if SCons.Util.is_String(s):
                    outdir.append(s)
                else:
                    outdir.append(s.get_abspath())
        else:
            outdir = [env['outdir'].get_abspath()]

        ##print 'from msvs.py; final value for string outdir is: ', outdir[0]
        self.finalout = outdir[0]
        self.bt = buildtarget[0]

        if not env.has_key('runfile') or env['runfile'] == None:
            runfile = buildtarget[-1:]
        elif SCons.Util.is_String(env['runfile']):
            runfile = [env['runfile']]
        elif SCons.Util.is_List(env['runfile']):
            if len(env['runfile']) != len(variants):
                raise SCons.Errors.InternalError, \
                    "Sizes of 'runfile' and 'variant' lists must be the same."
            runfile = []
            for s in env['runfile']:
                if SCons.Util.is_String(s):
                    runfile.append(s)
                else:
                    runfile.append(s.get_abspath())
        else:
            runfile = [env['runfile'].get_abspath()]
        if len(runfile) == 1:
            s = runfile[0]
            runfile = []
            for v in variants:
                runfile.append(s)

        self.sconscript = env['MSVSSCONSCRIPT']

        cmdargs = env.get('cmdargs', '')

        self.env = env

        if self.env.has_key('name'):
            self.name = self.env['name']
        elif buildtarget[0] != '':
            dir, nm = os.path.split(buildtarget[0])
            self.name = nm.split('.')[0]
            
        else:
            self.name = os.path.basename(SCons.Util.splitext(self.dspfile)[0])
        self.name = self.env.subst(self.name)

        sourcenames = [
            'Source Files',
            'Header Files',
            'Local Headers',
            'Resource Files',
            'Other Files']

        self.sources = {}
        for n in sourcenames:
            self.sources[n] = []

        self.configs = {}

        self.nokeep = 0
        if env.has_key('nokeep') and env['variant'] != 0:
            self.nokeep = 1

        if self.nokeep == 0 and os.path.exists(self.dspabs):
            self.Parse()

        for t in zip(sourcenames,self.srcargs):
            if self.env.has_key(t[1]):
                if SCons.Util.is_List(self.env[t[1]]):
                    for i in self.env[t[1]]:
                        if not i in self.sources[t[0]]:
                            self.sources[t[0]].append(i)
                else:
                    if not self.env[t[1]] in self.sources[t[0]]:
                        self.sources[t[0]].append(self.env[t[1]])

        self.targettype = ''
        if env.has_key('targettype'):
            self.targettype = self.env['targettype']

        self.installScript = ''
        if env.has_key('installScript'): 
            #print "found installScript in env:  ", env['installScript']
            self.installScript = env['installScript']

        for n in sourcenames:
            self.sources[n].sort(lambda a, b: cmp(string.lower(a), string.lower(b)))

        def AddConfig(self, variant, buildtarget, outdir, runfile, cmdargs, dspfile=dspfile):
            config = Config()
            config.buildtarget = buildtarget
            config.outdir = outdir
            config.cmdargs = cmdargs
            config.runfile = runfile

            match = re.match('(.*)\|(.*)', variant)
            if match:
                config.variant = match.group(1)
                config.platform = match.group(2)
            else:
                config.variant = variant
                config.platform = 'Win32'

            self.configs[variant] = config
            ##print "Adding '" + self.name + ' - ' + config.variant + '|' + config.platform + "' to '" + str(dspfile) + "'"

        for i in range(len(variants)):
            strOutdir = ''
            if SCons.Util.is_List(outdir): strOutdir = outdir[i]
            else: strOutdir = outdir
            AddConfig(self, variants[i], buildtarget[i], strOutdir,
                      runfile[i], cmdargs)

        self.platforms = []
        for key in self.configs.keys():
            platform = self.configs[key].platform
            if not platform in self.platforms:
                self.platforms.append(platform)

    def Build(self):
        pass


V7DSPHeader = """\
<?xml version="1.0" encoding = "%(encoding)s"?>
<VisualStudioProject
\tProjectType="Visual C++"
\tVersion="%(versionstr)s"
\tName="%(name)s"
%(scc_attrs)s
\tKeyword="MakeFileProj">
"""

V7DSPConfiguration = """\
\t\t<Configuration
\t\t\tName="%(variant)s|%(platform)s"
\t\t\tOutputDirectory="%(outdir)s"
\t\t\tIntermediateDirectory="%(outdir)s"
\t\t\tConfigurationType="0"
\t\t\tUseOfMFC="0"
\t\t\tATLMinimizesCRunTimeLibraryUsage="FALSE">
\t\t\t<Tool
\t\t\t\tName="VCNMakeTool"
\t\t\t\tBuildCommandLine="%(buildcmd)s"
\t\t\t\tCleanCommandLine="%(cleancmd)s"
\t\t\t\tRebuildCommandLine="%(rebuildcmd)s"
\t\t\t\tOutput="%(runfile)s"/>
\t\t</Configuration>
"""

## (jrb) This works for V9 as well as V8
V8DSPHeader = """\
<?xml version="1.0" encoding="%(encoding)s"?>
<VisualStudioProject
\tProjectType="Visual C++"
\tVersion="%(versionstr)s"
\tName="%(name)s"
%(scc_attrs)s
\tRootNamespace="%(name)s"
\tKeyword="MakeFileProj">
"""


##UNUSED V8DSPConfiguration = """\


## From HelloWorld; modified since
V8DSPConfiguration_header = """\
\t\t<Configuration
\t\t\tName="%(variant)s|Win32"
\t\t\tConfigurationType="%(confType)s"
\t\t\tIntermediateDirectory="$(ConfigurationName)\%(name)s"
\t\t\tBuildLogFile="$(IntDir)\%(name)sBuildLog.htm"
\t\t\tOutputDirectory="%(outdir)s"
\t\t\tUseOfMFC="0"
\t\t\tATLMinimizesCRunTimeLibraryUsage="false"
\t\t\t>
"""

V8DSPConfiguration_trailer = """\
\t\t</Configuration>
"""

## do we also want the following in V8VCCLCompilerTool ?
###  \t\t\t\tPreprocessorDefinitions="%(preprocdefs)s"
###  \t\t\t\tIncludeSearchPath="%(includepath)s"

# define data used to construct tools: this is a dictionary with the name of the tool as a key,
# and the value a list of attribute definitions, containing patterns to expand
V8VCCLCompilerTool = """
\t\t\t<Tool
\t\t\t\tName="VCCLCompilerTool"
\t\t\t\tPreprocessorDefinitions="WIN32"
\t\t\t\tOptimization="%(vsOptimize)s"
\t\t\t\tAdditionalOptions='%(moreCompileOptions)s'
\t\t\t\tAdditionalIncludeDirectories="%(additional_includes)s"
\t\t\t\tWarningLevel="3"
\t\t\t\tDetect64BitPortabilityProblems="false"
\t\t\t\tDebugInformationFormat="1"
\t\t\t\tRuntimeLibrary="%(rt_number)s"
\t\t\t\tForcedIncludeFiles="%(forcedInclude)s"
\t\t\t/>
"""

# A given project file has at most one of the following pre-build tools
V8VCSwigPrebuildTool = """
\t\t\t<Tool
\t\t\t\tName="VCPreBuildEventTool"
\t\t\t\tCommandLine='%(swigcmd)s'
\t\t\t/>
"""

V8VCRootcintPrebuildTool = """
\t\t\t<Tool
\t\t\t\tName="VCPreBuildEventTool"
\t\t\t\tCommandLine='%(rootcintcmd)s'
\t\t\t/>
"""

# For Gaudi programs copy common source files to work area
V8VCGaudiTestTool = """
\t\t\t<Tool
\t\t\t\tName="VCPreBuildEventTool"
\t\t\t\tCommandLine='xcopy /S /Y /F %(gr_app_src)s\setPriority.cxx $(IntDir)\ &amp;&amp; xcopy /S /Y /F %(gr_app_src)s\TestGlastMain.cxx $(IntDir)\'
\t\t\t/>
"""

V8VCGaudiMainTool = """
\t\t\t<Tool
\t\t\t\tName="VCPreBuildEventTool"
\t\t\t\tCommandLine='xcopy /S /Y /F %(gr_app_src)s\setPriority.cxx $(IntDir)\ &amp;&amp; xcopy /S /Y /F %(gr_app_src)s\GlastMain.cxx $(IntDir)\'
\t\t\t/>
"""

# Call ROOT bindexplib or other program to get necessary defs
V8VCPrelinkTool = """
\t\t\t<Tool
\t\t\t\tName="VCPreLinkEventTool"
\t\t\t\tCommandLine='%(prelink)s'
\t\t\t/>
"""

V8VCLinkLibTool = """
\t\t\t<Tool
\t\t\t\tName="VCLinkerTool"
\t\t\t\tAdditionalOptions='/dll  /def:%(name)s.def %(linkflags)s '
\t\t\t\tAdditionalLibraryDirectories="%(libpath)s"
\t\t\t\tAdditionalDependencies="%(libraries)s"
\t\t\t\tGenerateDebugInformation="true"
\t\t\t\tGenerateManifest="true"
\t\t\t\tManifestFile="%(name)s.manifest"
\t\t\t\tOutputFile="%(outdir)s\\%(name)s.%(linkfileext)s"
\t\t\t\tSubSystem="1"
\t\t\t\tTargetMachine="1"
\t\t\t/>
"""

V8VCLinkStaticLibTool = """
\t\t\t<Tool
\t\t\t\tName="VCLibrarianTool"
\t\t\t\tOutputFile="%(outdir)s\\%(name)s.%(linkfileext)s"
\t\t\t/>
"""

V8VCLinkExeTool = """
\t\t\t<Tool
\t\t\t\tName="VCLinkerTool"
\t\t\t\tAdditionalOptions="%(linkflags)s "
\t\t\t\tAdditionalLibraryDirectories="%(libpath)s"
\t\t\t\tAdditionalDependencies="%(libraries)s"
\t\t\t\tGenerateDebugInformation="true"
\t\t\t\tGenerateManifest="true"
\t\t\t\tManifestFile="%(name)s.manifest"
\t\t\t\tSubSystem="1"
\t\t\t\tTargetMachine="1"
\t\t\t\tOutputFile="%(outdir)s\\%(name)s.%(linkfileext)s"
\t\t\t/>
"""

# Run a file created by makeStudio which copies headers, job options, etc. to install location
V8VCInstallTool = """
\t\t\t<Tool
\t\t\t\tName="VCPostBuildEventTool"
\t\t\t\tCommandLine="%(installScript)s"
\t\t\t/>
"""

# Same as above but for projects which don't do anything else
V8VCInstallOnlyTool = """
\t\t\t<Tool
\t\t\t\tName="VCNMakeTool"
\t\t\t\tBuildCommandLine="%(installScript)s"
\t\t\t\tReBuildCommandLine="%(installScript)s"
\t\t\t/>
"""

class _GenerateV7DSP(_DSPGenerator):
    """Generates a Project file for MSVS .NET"""

    def __init__(self, dspfile, source, env):
        #print 'in _GenerateV7DSP.__init__'
        _DSPGenerator.__init__(self, dspfile, source, env)
        self.version = env['MSVS_VERSION']
        self.version_num, self.suite = msvs_parse_version(self.version)
        if self.version_num >=8.0:
            if self.version_num == 9.0:
                self.versionstr = '9.00'
            else:
                self.versionstr = '8.00'
            self.dspheader                = V8DSPHeader
            self.dspconfiguration_header  = V8DSPConfiguration_header
            self.dspconfiguration_trailer = V8DSPConfiguration_trailer
            self.ccflags                  = self.env.subst('$CCFLAGS')
            self.vsOptimize               = "0"
            self.confType                 = 0    # init to unknown

            #self.moreCompileOptions = self.env.subst('$CXXFLAGS $CCFLAGS $_CCCOMCOM')
            # Take out $CXXFLAGS since options accumulated here will be applied
            # to all compiles and may not be appropriate for .c
            self.moreCompileOptions = self.env.subst('$CCFLAGS $_CCCOMCOM')

            # Replace all instances of /I#  with /I..\..\ (/I..\ if no variant)
            if 'NO_VARIANT' in self.env: incString = "/I..\\"
            else: incString = "/I..\\..\\"
            self.moreCompileOptions = (self.moreCompileOptions).replace("/I#", 
                                                                      incString)
	    varCmps = str(env['VISUAL_VARIANT']).split("-")
	    if "Debug" in varCmps: 
                self.rt_number="3"
            else: 
                self.rt_number="2"
            if env.has_key('buildtarget') and env['buildtarget'] != None and env['buildtarget'] != "*DUMMY*":
                buildt = [self.env.File(env['buildtarget'])]
                cmps = (env['buildtarget']).split('.')
                if len(cmps) == 2:
                    self.linkfileext = cmps[1]
            else:
                self.linkfileext              = "exe"

            if self.linkfileext == "dll":
                pass
                
            elif self.targettype == "rootcintlib":
                self.DoRootcint()

            #  set additional_includes to be package-root and package-root/src
            self.additional_includes      = ""
            if env.has_key('packageroot'):
                self.additional_includes = env['packageroot'] + ";" + os.path.join(str(env['packageroot']), 'src')

            #  Do we always want runtimelibrary = 2 ?  Probably not.
            #  It dictates whether we get MSVCRTD, MSVCRT, etc.
            self.runtimelibrary           = "2"
            self.forcedInclude            = ""
                
            self.linkflags                = self.env.subst('$LINKFLAGS')
            libpath_env                   = self.env.subst('$LIBPATH')
            libdirs = libpath_env.split()
            self.libpath = ';'.join(libdirs)

            liblist = self.env.subst('$LIBS').split()
            self.libraries                = ""
            for tok in liblist:
                if self.linkfileext == 'dll' and tok == self.name:
                    continue
                tok += '.lib'
                self.libraries += " " + tok
                #print "variant: ", env['variant']

        else:
            if self.version_num >= 7.1:
                self.versionstr = '7.10'
            else:
                self.versionstr = '7.00'
            self.dspheader = V7DSPHeader
            self.dspconfiguration = V7DSPConfiguration
        self.file = None

    def DoRootcint(self):
        # Figure out how to write out rootcint command.
        #  sources for the rootcint node *should* be what we
        # want..
        rootcintnode = self.env['rootcint_node']
        #print "inside DoRootcint with rootcintnode ", str(rootcintnode)
        rootcintsrcnodes = self.env.FindSourceFiles(node=rootcintnode)
        rootcintsrcnames = []
        for v in rootcintsrcnodes:
            rootcintsrcnames.append(str(v.srcnode().abspath))
        #print 'Sources for rootcint are: ', rootcintsrcnames
        #print 'Target is: ', rootcintnode[0].srcnode().abspath
        rootcintfname = (os.path.split(rootcintnode[0].abspath))[1]

        derivedsrc =  rootcintfname
        self.sources["Source Files"].append(derivedsrc)
        derivedinc = derivedsrc.replace('.cxx', '.h')
        self.sources["Header Files"].append(derivedinc)                    

        fileContents = 'rootcint -f ' + rootcintfname
        if self.env.get('CONTAINERNAME','') != 'GlastRelease':
            fileContents += ' -c -I..\\..\\include'
        else:
            fileContents += ' -c -I'+self.env['packageroot']
            # Also need to add any other extra include paths
            for p in self.env['CPPPATH']:
                q = str(p).replace("#", "..\\..\\")
                fileContents += ' -I'+q
        linkdefentry = ''
        for nm in rootcintsrcnames:
            if nm.find("LinkDef") == -1:
                fileContents += ' ' + nm
            else:
                linkdefentry = ' ' + nm + '\n'

        if linkdefentry == '':
            print 'No LinkDef file!'
            print 'Cannot write good rootcint command'
            return
        fileContents += linkdefentry
        fileContents += '\n'
                    
        #print 'rootcintcmd is to be written to a file is: '
        #print fileContents
        #print ' ----  end rootcintcmd ---- '

        # Now write it to a file in Studio's working dir.
        filename = self.name + "_rootcint.bat"
        fullpath = str(self.env['STUDIODIR']) + '\\' + filename
        rootcintFile = open(fullpath, 'w')
        #print "opened file at path ", str(fullpath)
        #print " resulting file object: ", str(rootcintFile)
        rootcintFile.write(fileContents)
        rootcintFile.close()
        self.rootcintcmd = filename

    def GetSources(self):
        env = self.env
        if self.targettype == "install": return

        shobjSuff = env['OBJSUFFIX'] + " "
        # Now use cfile_re pattern to replace .cxx or .c with OBJSUFFIX
        def _toObj(matchObj):
            return shobjSuff

        confkeys = self.configs.keys()
        confkeys.sort()
        #  There really is only one thing in confkeys.

        outfile = os.path.join(self.finalout, self.bt)

        foundSources = env.FindSourceFiles(node=File(outfile))

        #print "Inside GetSources for buildtarget ", str(outfile), " found: "
        #for s in foundSources:
        #    print str(s)
            
        usedSources=[]

        if self.targettype == "swigdll":
            # set misc to the .i file

            for v in foundSources:
                vname = (os.path.split(v.abspath))[1]
                #if (_isSomething(vname,'i')):
                cmps = vname.split(".")
                if (len(cmps) == 2) and ((cmps[1] == 'i')):
                    # look for 'build' in path
                    fdebug('Found .i file %s' % str(v) )
                    vv = v
                    avcmps = str(v.abspath).split("\\")
                    if "build" in avcmps:
                        fdebug('found "build" in avcmps')
                        ix = avcmps.index("build")
                        nxt = avcmps[ix+1]
                        avcmps.remove("build")
                        avcmps.remove(nxt)
                        vv = '\\'.join(avcmps)

                    fdebug('vv is %s' % str(vv))
                    usedSources.append(str(vv))
                    env['misc'] = usedSources

        else:                # not swigdll
            # bindexplib.exe and link.exe are include in list
            # returned by FindSourceFiles, so explicitly exclude
            # For root libs, headers can sneak in as sources; throw them out also
            if self.targettype == "rootcintdll": 
                foundSources.append(self.env['rootcint_node'][0])

            for v in foundSources:
                ##vname = (os.path.split(v.abspath))[1]  do we need the abspath?
                pcmps = os.path.split(str(v))
                vname = pcmps[1]
                #print "Got vname ", vname
                cmps = vname.split(".")
                if not ((len(cmps) == 2) and ((cmps[1] == 'exe') or (cmps[1] == 'EXE')
                                              or (cmps[1] == 'h') or (cmps[1] == 'H'))):
                    # look for 'build' in path
                    avcmps = str(v.abspath).split("\\")
                    vv = vname
                    if "build" in avcmps:
                        ix = avcmps.index("build")
                        nxt = avcmps[ix+1]
                        avcmps.remove("build")
                        avcmps.remove(nxt)
                        vv = '\\'.join(avcmps)

                    #print "from ", str(v), " created ", vv
                    usedSources.append(vv)
                    
            self.env['src'] = usedSources
            for u in usedSources: self.sources['Source Files'].append(u)
            #print "GetSources:  'Source Files entry:"
            #for i in self.sources['Source Files']: print str(i)

        if self.linkfileext == "dll":
            shlink0 = self.env['SHLINKCOM'].list[0].cmd_list
            buildt = [self.env.File(self.env['buildtarget'])]
            if self.targettype == "dll":
                self.prelink = env.subst(shlink0, target=buildt,
                                         source=usedSources)

            elif self.targettype == "swigdll":
                # only source is .cc file created by swig step
                ifile = env['misc'][0]
                ifilename = os.path.split(ifile)[1]
                derivedsrc = env['variant'] + '\\' + ifilename.split(".")[0] + '_wrap.cc'
                self.env['src'] = [derivedsrc]
                self.sources["Source Files"].append(derivedsrc)
                self.prelink = env.subst(shlink0, target=buildt,
                                         source=[derivedsrc])
                self.swigcmd = 'swig.exe -o ' + derivedsrc + ' '
                swigincs = ''

                for p in Flatten(self.env['SWIGPATH']):
                    #print 'p is: ', p
                    #print 'type p is: ', type(p)
                    if isinstance(p,str): swigincs += ' -I' + os.path.abspath(p)
                    else:  swigincs += ' -I' + p.abspath
                            
                self.swigcmd += swigincs
                self.swigcmd += ' '  + self.env['SWIGFLAGS']
                self.swigcmd += ' ' + ifile 
                #print 'swigcmd is: ', self.swigcmd

            elif self.targettype == "rootcintdll":
                self.prelink = self.env.subst(shlink0,
                                              target=buildt,
                                              source=self.sources['Source Files'])
                #  Writing rootcint command. Sources for the rootcint 
                #node *should* be what we
                self.DoRootcint()

            aftersub = cfile_re.sub(_toObj, self.prelink)
            # print 'after re _toObj sub: ', aftersub

            # Working directory subdir of variant dir is named after target
            vr = ' ' + env['variant'] + '\\'+ self.name + '\\'
            def _toVarDir(matchObj):
                return  vr + matchObj.group('f')

            # ..and now use cfiledir_re to get proper directory
            aftersub2 = cfiledir_re.sub(_toVarDir, aftersub)
            #print 'after re sub for  correct directory: ', aftersub2
            self.prelink = aftersub2

        elif self.targettype == "rootcintlib":
            self.DoRootcint()

    def PrintHeader(self):
        env = self.env
        versionstr = self.versionstr
        name = self.name
        encoding = self.env.subst('$MSVSENCODING')
        scc_provider = env.get('MSVS_SCC_PROVIDER', '')
        scc_project_name = env.get('MSVS_SCC_PROJECT_NAME', '')
        scc_aux_path = env.get('MSVS_SCC_AUX_PATH', '')
        scc_local_path = env.get('MSVS_SCC_LOCAL_PATH', '')
        project_guid = env.get('MSVS_PROJECT_GUID', '')
        if self.version_num >= 8.0 and not project_guid:
            project_guid = _generateGUID(self.dspfile, '')
        if scc_provider != '':
            scc_attrs = ('\tProjectGUID="%s"\n'
                         '\tSccProjectName="%s"\n'
                         '\tSccAuxPath="%s"\n'
                         '\tSccLocalPath="%s"\n'
                         '\tSccProvider="%s"' % (project_guid, scc_project_name, scc_aux_path, scc_local_path, scc_provider))
        else:
            scc_attrs = ('\tProjectGUID="%s"\n'
                         '\tSccProjectName="%s"\n'
                         '\tSccLocalPath="%s"' % (project_guid, scc_project_name, scc_local_path))

        self.file.write(self.dspheader % locals())

        self.file.write('\t<Platforms>\n')
        for platform in self.platforms:
            self.file.write(
                        '\t\t<Platform\n'
                        '\t\t\tName="%s"/>\n' % platform)
        self.file.write('\t</Platforms>\n')

        if self.version_num >= 8.0:
            self.file.write('\t<ToolFiles>\n'
                            '\t</ToolFiles>\n')

    ## From HelloWorld

    def PrintProject(self):
        self.file.write('\t<Configurations>\n')

        confkeys = self.configs.keys()
        confkeys.sort()
        name = self.name
        for kind in confkeys:
            variant = self.configs[kind].variant
            platform = self.configs[kind].platform
            outdir = self.configs[kind].outdir
            buildtarget = self.configs[kind].buildtarget
            runfile     = self.configs[kind].runfile
            cmdargs = self.configs[kind].cmdargs

            env_has_buildtarget = self.env.has_key('MSVSBUILDTARGET')
            if not env_has_buildtarget:
                self.env['MSVSBUILDTARGET'] = buildtarget

            starting = 'echo Starting SCons && '
            if cmdargs:
                cmdargs = ' ' + cmdargs
            else:
                cmdargs = ''
            buildcmd    = xmlify(starting + self.env.subst('$MSVSBUILDCOM', 1) + cmdargs)
            rebuildcmd  = xmlify(starting + self.env.subst('$MSVSREBUILDCOM', 1) + cmdargs)
            cleancmd    = xmlify(starting + self.env.subst('$MSVSCLEANCOM', 1) + cmdargs)

            if not env_has_buildtarget:
                del self.env['MSVSBUILDTARGET']

            ## from HelloWorld. Break configuration description into pieces
            self.outdir = ''
            if (len(outdir) > 0):
                self.outdir = outdir
            if self.linkfileext == "dll":    confType = 2
            elif  self.linkfileext == "lib": confType = 4
            elif self.linkfileext == "exe": confType = 1
            # if we're just doing install, ignore everything else.
            if self.targettype == "install": confType = 0

            #print "About to write V8DSPConfigure_header"
            self.file.write(self.dspconfiguration_header % locals())


            # Within dll case, need to distinguish between swig lib and
            # non-swig.  
            if self.linkfileext == "dll":
                #if not self.env.has_key('srcs'):
                if self.targettype == 'swigdll':
                    # It's swig
                    self.file.write(V8VCSwigPrebuildTool % self.__dict__)
                    # add output of swig command to file srcs??
                    # form is <libname>_wrap.cc, e.g. py_facilities_wrap.cc
                elif self.targettype == 'rootcintdll':
                    self.file.write(V8VCRootcintPrebuildTool % self.__dict__)
                    
                self.file.write(V8VCCLCompilerTool % self.__dict__)
                self.file.write(V8VCPrelinkTool % self.__dict__)
                self.file.write(V8VCLinkLibTool % self.__dict__)
            elif self.linkfileext == "lib":
                if self.targettype == 'rootcintlib':
                    self.file.write(V8VCRootcintPrebuildTool % self.__dict__)
                self.file.write(V8VCCLCompilerTool % self.__dict__)
                self.file.write(V8VCLinkStaticLibTool % self.__dict__)
            elif self.linkfileext == "exe":
                gaudi = self.env.get('GAUDIPROG','')
                if gaudi == 'test':
                    self.file.write(V8VCGaudiTestTool % self.__dict__)
                elif gaudi == 'main':
                    self.file.write(V8VCGaudiMainTool % self.__dict__)
                if self.targettype != "install":
                    self.file.write(V8VCCLCompilerTool % self.__dict__)
                    self.file.write(V8VCLinkExeTool % self.__dict__)

            # If we were passed an installScript add either PostBuildEvent step
            # or fake VCNMakeTool (in case we're not building anything else)
            #print "self.installScript is: ", self.installScript
            if self.installScript != '':
                if self.targettype == "install":
                    self.file.write(V8VCInstallOnlyTool % self.__dict__)
                else:
                    self.file.write(V8VCInstallTool % self.__dict__)

            self.file.write(self.dspconfiguration_trailer % locals())
            ## end of HelloWorld stuff with additions


        self.file.write('\t</Configurations>\n')

        if self.version_num >= 7.1:
            self.file.write('\t<References>\n'
                            '\t</References>\n')

        self.PrintSourceFiles()

        self.file.write('</VisualStudioProject>\n')

    def printSources(self, hierarchy, commonprefix):
        sorteditems = hierarchy.items()
        sorteditems.sort(lambda a, b: cmp(string.lower(a[0]),
                                          string.lower(b[0])))

        # First folders, then files
        for key, value in sorteditems:
            if SCons.Util.is_Dict(value):
                self.file.write('\t\t\t<Filter\n'
                                '\t\t\t\tName="%s"\n'
                                '\t\t\t\tFilter="">\n' % (key))
                self.printSources(value, commonprefix)
                self.file.write('\t\t\t</Filter>\n')

        for key, value in sorteditems:
            if SCons.Util.is_String(value):
                file = value
                if commonprefix:
                    file = os.path.join(commonprefix, value)
                file = os.path.normpath(file)
                self.file.write('\t\t\t<File\n'
                                '\t\t\t\tRelativePath="%s">\n'
                                '\t\t\t</File>\n' % (file))

    def PrintSourceFiles(self):
        categories = {'Source Files': 'cpp;c;cxx;cc;l;y;def;odl;idl;hpj;bat',
                      'Header Files': 'h;hpp;hxx;hm;inl',
                      'Local Headers': 'h;hpp;hxx;hm;inl',
                      'Resource Files': 'r;rc;ico;cur;bmp;dlg;rc2;rct;bin;cnt;rtf;gif;jpg;jpeg;jpe',
                      'Other Files': ''}

        self.file.write('\t<Files>\n')

        cats = categories.keys()
        cats.sort(lambda a, b: cmp(string.lower(a), string.lower(b)))
        cats = filter(lambda k, s=self: s.sources[k], cats)
        for kind in cats:
            if len(cats) > 1:
                self.file.write('\t\t<Filter\n'
                                '\t\t\tName="%s"\n'
                                '\t\t\tFilter="%s">\n' % (kind, categories[kind]))

            sources = self.sources[kind]

            # For gaudi programs, a couple files are handled specially.  For VS they will be found
            # in intermediate directory
            if kind == "Source Files":
                gaudi = self.env.get('GAUDIPROG','')
                if gaudi != '':
                    #print "sources for gaudi program are"
                    #for s in sources:  print(str(s))
                    toRemove = []
                    toAppend = []
                    for s in sources:
                        if 'setPriority'  in s:
                            toRemove.append(s)
                            toAppend.append(os.path.join("Visual-vc90-Debug", self.name, "setPriority.cxx"))
                        if 'GlastMain' in s:
                            toRemove.append(s)
                            if gaudi == 'test':
                                toAppend.append(os.path.join("Visual-vc90-Debug", self.name, "TestGlastMain.cxx"))
                            elif gaudi == 'main':
                                toAppend.append(os.path.join("Visual-vc90-Debug", self.name, "GlastMain.cxx"))
                    for s in toRemove: sources.remove(s)
                    for s in toAppend: sources.append(s)
            # First remove any common prefix
            commonprefix = None
            if len(sources) > 1:
                s = map(os.path.normpath, sources)
                # take the dirname because the prefix may include parts
                # of the filenames (e.g. if you have 'dir\abcd' and
                # 'dir\acde' then the cp will be 'dir\a' )
                cp = os.path.dirname( os.path.commonprefix(s) )
                if cp and s[0][len(cp)] == os.sep:
                    # +1 because the filename starts after the separator
                    sources = map(lambda s, l=len(cp)+1: s[l:], sources)
                    commonprefix = cp
            elif len(sources) == 1:
                commonprefix = os.path.dirname( sources[0] )
                sources[0] = os.path.basename( sources[0] )

            hierarchy = makeHierarchy(sources)
            self.printSources(hierarchy, commonprefix=commonprefix)

            if len(cats)>1:
                self.file.write('\t\t</Filter>\n')

        # add the SConscript file outside of the groups
        # jrb - no, don't.  We don't need it. 

        self.file.write('\t</Files>\n'
                        '\t<Globals>\n'
                        '\t</Globals>\n')

    def Parse(self):
        pass

    def Build(self):
        #print 'In _GenerateV7DSP.Build'
        try:
            self.file = open(self.dspabs,'w')
        except IOError, detail:
            raise SCons.Errors.InternalError, 'Unable to open "' + self.dspabs + '" for writing:' + str(detail)
        else:
            self.PrintHeader()
            self.GetSources()
            self.PrintProject()
            self.file.close()

class _DSWGenerator:
    """ Base class for DSW generators """
    def __init__(self, dswfile, source, env):
        #print 'From _DSWGenerator.__init__'
        self.dswfile = os.path.normpath(str(dswfile))
        self.env = env

        if not env.has_key('projects'):
            raise SCons.Errors.UserError, \
                "You must specify a 'projects' argument to create an MSVSSolution."
        projects = env['projects']
        if not SCons.Util.is_List(projects):
            raise SCons.Errors.InternalError, \
                "The 'projects' argument must be a list of nodes."
        projects = SCons.Util.flatten(projects)
        if len(projects) < 1:
            raise SCons.Errors.UserError, \
                "You must specify at least one project to create an MSVSSolution."
        self.dspfiles = map(str, projects)

        if self.env.has_key('name'):
            self.name = self.env['name']
        else:
            self.name = os.path.basename(SCons.Util.splitext(self.dswfile)[0])
        self.name = self.env.subst(self.name)

    def Build(self):
        pass

## in spite of the misleading name, this handles VS 8.0 and 9.0 as well as 7
class _GenerateV7DSW(_DSWGenerator):
    """Generates a Solution file for MSVS .NET"""
    def __init__(self, dswfile, source, env):
        _DSWGenerator.__init__(self, dswfile, source, env)

        self.file = None
        self.version = self.env['MSVS_VERSION']
        self.version_num, self.suite = msvs_parse_version(self.version)
        self.versionstr = '7.00'
        if self.version_num >= 8.0:
            self.versionstr = '9.00'
        elif self.version_num >= 7.1:
            self.versionstr = '8.00'
        if self.version_num > 8.0:
            self.versionstr = '9.00'

        if env.has_key('slnguid') and env['slnguid']:
            self.slnguid = env['slnguid']
        else:
            self.slnguid = _generateGUID(dswfile, self.name)

        self.configs = {}

        self.nokeep = 0
        if env.has_key('nokeep') and env['variant'] != 0:
            self.nokeep = 1

        ##  Machinery for dependencies among projects in the solution
        ##  Dictionary of values of LIBS var for each project.  Key
        ##  is file name (not including directory or extension)
        if env.has_key('libs'):
            self.projectLibs = env['libs']

        if env.has_key('installDir'):
            self.installDir = env['installDir']
            #print 'installdir is ', self.installDir
        else:
            self.installDir = ''
        if self.nokeep == 0 and os.path.exists(self.dswfile):
            self.Parse()

        def AddConfig(self, variant, dswfile=dswfile):
            config = Config()

            match = re.match('(.*)\|(.*)', variant)
            if match:
                config.variant = match.group(1)
                config.platform = match.group(2)
            else:
                config.variant = variant
                config.platform = 'Win32'

            self.configs[variant] = config
            #print "Adding '" + self.name + ' - ' + config.variant + '|' + config.platform + "' to '" + str(dswfile) + "'"

        if not env.has_key('variant'):
            raise SCons.Errors.InternalError, \
                  "You must specify a 'variant' argument (i.e. 'Debug' or " +\
                  "'Release') to create an MSVS Solution File."
        elif SCons.Util.is_String(env['variant']):
            AddConfig(self, env['variant'])
        elif SCons.Util.is_List(env['variant']):
            for variant in env['variant']:
                AddConfig(self, variant)

        self.platforms = []
        for key in self.configs.keys():
            platform = self.configs[key].platform
            if not platform in self.platforms:
                self.platforms.append(platform)

    def Parse(self):
        pass
    
    def PrintSolution(self):
        """Writes a solution file"""

        if self.version_num >= 9.0:
            self.versionstr = '10.00'
        self.file.write('Microsoft Visual Studio Solution File, Format Version %s\n' % self.versionstr )
        if self.version_num >= 9.0:
            self.file.write('# Visual Studio 2008\n')
        elif self.version_num >= 8.0:
            self.file.write('# Visual Studio 2005\n')
        for p in self.dspfiles:
            name = os.path.basename(p)
            base, suffix = SCons.Util.splitext(name)
            if suffix == '.vcproj':
                name = base
            #print "working on dspfiles entry ", name
            guid = _generateGUID(p, '')
            self.file.write('Project("%s") = "%s", "%s", "%s"\n'
                            % ( external_makefile_guid, name, p, guid ) )
            if self.version_num >= 7.1 and self.version_num < 8.0:
                self.file.write('\tProjectSection(ProjectDependencies) = postProject\n'
                                '\tEndProjectSection\n')
            elif self.version_num >=9.0:
                self.file.write('\tProjectSection(ProjectDependencies) = postProject\n')
                # Use 'name' above to look up assoc. libs for this project
                super = self.env.GetOption('supersede') != '.' 
                if super:
                    pkgs = list(os.path.basename(i) for i in self.env['packageNameList'])
                if self.projectLibs.has_key(name):
                    #print 'found key in projectLibs for ', name
                    for usedLib in self.projectLibs[name]:
                        #print "Processing usedLib ", usedLib
                        if super and (usedLib not in pkgs): 
                            #print usedLib, " will not be included in dependencies"
                            pass
                        else:
                            usedLib += 'Lib.vcproj'
                            if self.installDir != '':
                                usedLib = os.path.join(self.installDir, usedLib)
                            # Get *its* base name & use to compute guid
                            # Not necessary - already is just basename
                            usedGuid = _generateGUID(usedLib,'')
                            # Write a line that looks like
                            #    <lib-guid> = <lib-guid>
                            self.file.write('\t\t%s = %s\n'
                                            % (usedGuid, usedGuid) )
                else:
                    fdebug('No key found in projectLibs for %s ' % name)
                    
                # Finally end the project dependencies section
                self.file.write('\tEndProjectSection\n')
            self.file.write('EndProject\n')

        self.file.write('Global\n')

        env = self.env
        ## Probably could dispense with this 'if' and statements in its scope 
        if env.has_key('MSVS_SCC_PROVIDER'):
            dspfile_base = os.path.basename(self.dspfile)
            slnguid = self.slnguid
            scc_provider = env.get('MSVS_SCC_PROVIDER', '')
            scc_provider = string.replace(scc_provider, ' ', r'\u0020')
            scc_project_name = env.get('MSVS_SCC_PROJECT_NAME', '')
            scc_local_path = env.get('MSVS_SCC_LOCAL_PATH', '')
            scc_project_base_path = env.get('MSVS_SCC_PROJECT_BASE_PATH', '')
            # project_guid = env.get('MSVS_PROJECT_GUID', '')

            self.file.write('\tGlobalSection(SourceCodeControl) = preSolution\n'
                            '\t\tSccNumberOfProjects = 2\n'
                            '\t\tSccProjectUniqueName0 = %(dspfile_base)s\n'
                            '\t\tSccLocalPath0 = %(scc_local_path)s\n'
                            '\t\tCanCheckoutShared = true\n'
                            '\t\tSccProjectFilePathRelativizedFromConnection0 = %(scc_project_base_path)s\n'
                            '\t\tSccProjectName1 = %(scc_project_name)s\n'
                            '\t\tSccLocalPath1 = %(scc_local_path)s\n'
                            '\t\tSccProvider1 = %(scc_provider)s\n'
                            '\t\tCanCheckoutShared = true\n'
                            '\t\tSccProjectFilePathRelativizedFromConnection1 = %(scc_project_base_path)s\n'
                            '\t\tSolutionUniqueID = %(slnguid)s\n'
                            '\tEndGlobalSection\n' % locals())

        if self.version_num >= 8.0:
            self.file.write('\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')
        else:
            self.file.write('\tGlobalSection(SolutionConfiguration) = preSolution\n')

        confkeys = self.configs.keys()
        confkeys.sort()
        cnt = 0
        for name in confkeys:
            variant = self.configs[name].variant
            platform = self.configs[name].platform
            if self.version_num >= 8.0:
                self.file.write('\t\t%s|%s = %s|%s\n' % (variant, platform, variant, platform))
            else:
                self.file.write('\t\tConfigName.%d = %s\n' % (cnt, variant))
            cnt = cnt + 1
        self.file.write('\tEndGlobalSection\n')
        if self.version_num < 7.1:
            self.file.write('\tGlobalSection(ProjectDependencies) = postSolution\n'
                            '\tEndGlobalSection\n')
        if self.version_num >= 8.0:
            self.file.write('\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
        else:
            self.file.write('\tGlobalSection(ProjectConfiguration) = postSolution\n')

        for name in confkeys:
            variant = self.configs[name].variant
            platform = self.configs[name].platform
            if self.version_num >= 8.0:
                for p in self.dspfiles:
                    guid = _generateGUID(p, '')
                    self.file.write('\t\t%s.%s|%s.ActiveCfg = %s|%s\n'
                                    '\t\t%s.%s|%s.Build.0 = %s|%s\n'  % (guid,variant,platform,variant,platform,guid,variant,platform,variant,platform))
            else:
                for p in self.dspfiles:
                    guid = _generateGUID(p, '')
                    self.file.write('\t\t%s.%s.ActiveCfg = %s|%s\n'
                                    '\t\t%s.%s.Build.0 = %s|%s\n'  %(guid,variant,variant,platform,guid,variant,variant,platform))

        self.file.write('\tEndGlobalSection\n')

        if self.version_num >= 8.0:
            self.file.write('\tGlobalSection(SolutionProperties) = preSolution\n'
                            '\t\tHideSolutionNode = FALSE\n'
                            '\tEndGlobalSection\n')
        else:
            self.file.write('\tGlobalSection(ExtensibilityGlobals) = postSolution\n'
                            '\tEndGlobalSection\n'
                            '\tGlobalSection(ExtensibilityAddIns) = postSolution\n'
                            '\tEndGlobalSection\n')
        self.file.write('EndGlobal\n')

    def Build(self):
        try:
            self.file = open(self.dswfile,'w')
        except IOError, detail:
            raise SCons.Errors.InternalError, 'Unable to open "' + self.dswfile + '" for writing:' + str(detail)
        else:
            self.PrintSolution()
            self.file.close()


def GenerateDSP(dspfile, source, env):
    """Generates a Project file based on the version of MSVS that is being used"""
    version_num = 6.0
    if env.has_key('MSVS_VERSION'):
        version_num, suite = msvs_parse_version(env['MSVS_VERSION'])
    if version_num >= 7.0:
        g = _GenerateV7DSP(dspfile, source, env)
        g.Build()
    else:
        raise SCons.Errors.InternalError, 'VS 6.0 not supported'
        

def GenerateDSW(dswfile, source, env):
    """Generates a Solution/Workspace file based on the version of MSVS that is being used"""

    version_num = 6.0
    if env.has_key('MSVS_VERSION'):
        version_num, suite = msvs_parse_version(env['MSVS_VERSION'])
    if version_num >= 7.0:
        g = _GenerateV7DSW(dswfile, source, env)
        g.Build()
    else:
        raise SCons.Errors.InternalError, 'VS 6.0 not supported'


##############################################################################
# Above here are the classes and functions for generation of
# DSP/DSW/SLN/VCPROJ files.
##############################################################################

# TODO(sgk):  eliminate in favor of direct calls to get_default_version()
if sys.platform == 'win32':
    def get_default_visualstudio_version(env):
        from SCons.Tool.MSVCCommon import get_default_version
        return get_default_version(env)

    # TODO(sgk):  eliminate in favor of direct calls to query_versions()
    def get_visualstudio_versions():
        from SCons.Tool.MSVCCommon import query_versions
        return query_versions()

    # TODO(sgk):  eliminate in favor of some other wrapper
    def get_msvs_install_dirs(key=None):
        from SCons.Tool.MSVCCommon.findloc import find_msvs_paths
        from SCons.Tool.MSVCCommon import query_versions
        if not key:
            vers = query_versions()
            if len(vers) > 0:
                ver = vers[0]
            else:
                ver = 9.0
            flav = 'std'
        else:
            verstr, flav = msvs_parse_version(key)
            ver = float(verstr)
            if not flav:
                flav = 'std'
            else:
                if flav == 'Exp':
                    flav = 'express'

        return find_msvs_paths(ver, flav)

def GetMSVSProjectSuffix(target, source, env, for_signature):
     return env['MSVS']['PROJECTSUFFIX']

def GetMSVSSolutionSuffix(target, source, env, for_signature):
     return env['MSVS']['SOLUTIONSUFFIX']

def GenerateProject(target, source, env):
    # generate the dsp file, according to the version of MSVS.
    # jrb.   Try switching...
    #builddspfile = target[0]          Original SCons code
    #dspfile = builddspfile.srcnode()  Original SCons code

    # Instead let dspfile be specified target (which is in variant dir)
    dspfile = target[0]
    #print 'In GenerateProject. After reversal..'
    #print 'dspfile = target[0] = ', dspfile
    builddspfile = dspfile.srcnode()
    #print 'builddspfile = dspfile.srcnode() = ', builddspfile
    # this detects whether or not we're using a VariantDir
    if not dspfile is builddspfile:
        try:
            bdsp = open(str(builddspfile), "w+")
        except IOError, detail:
            print 'Unable to open "' + str(dspfile) + '" for writing:',detail,'\n'
            raise

        bdsp.write("This is just a placeholder file.\nThe real project file is here:\n%s\n" % dspfile.get_abspath())

    GenerateDSP(dspfile, source, env)

    if env.get('auto_build_solution', 1):
        builddswfile = target[1]
        dswfile = builddswfile.srcnode()

        if not dswfile is builddswfile:

            try:
                bdsw = open(str(builddswfile), "w+")
            except IOError, detail:
                print 'Unable to open "' + str(dspfile) + '" for writing:',detail,'\n'
                raise

            bdsw.write("This is just a placeholder file.\nThe real workspace file is here:\n%s\n" % dswfile.get_abspath())

        GenerateDSW(dswfile, source, env)

def GenerateSolution(target, source, env):
    GenerateDSW(target[0], source, env)

def projectEmitter(target, source, env):
    """Sets up the DSP dependencies."""

    # todo: Not sure what sets source to what user has passed as target,
    # but this is what happens. When that is fixed, we also won't have
    # to make the user always append env['MSVSPROJECTSUFFIX'] to target.
    if source[0] == target[0]:
        source = []

    # make sure the suffix is correct for the version of MSVS we're running.
    (base, suff) = SCons.Util.splitext(str(target[0]))
    suff = env.subst('$MSVSPROJECTSUFFIX')
    target[0] = base + suff

    if not source:
        source = 'prj_inputs:'
        source = source + env.subst('$MSVSSCONSCOM', 1)
        source = source + env.subst('$MSVSENCODING', 1)

        if env.has_key('buildtarget') and env['buildtarget'] != None:
            if SCons.Util.is_String(env['buildtarget']):
                source = source + ' "%s"' % env['buildtarget']
            elif SCons.Util.is_List(env['buildtarget']):
                for bt in env['buildtarget']:
                    if SCons.Util.is_String(bt):
                        source = source + ' "%s"' % bt
                    else:
                        try: source = source + ' "%s"' % bt.get_abspath()
                        except AttributeError: raise SCons.Errors.InternalError, \
                            "buildtarget can be a string, a node, a list of strings or nodes, or None"
            else:
                try: source = source + ' "%s"' % env['buildtarget'].get_abspath()
                except AttributeError: raise SCons.Errors.InternalError, \
                    "buildtarget can be a string, a node, a list of strings or nodes, or None"

        if env.has_key('outdir') and env['outdir'] != None:
            if SCons.Util.is_String(env['outdir']):
                source = source + ' "%s"' % env['outdir']
            elif SCons.Util.is_List(env['outdir']):
                for s in env['outdir']:
                    if SCons.Util.is_String(s):
                        source = source + ' "%s"' % s
                    else:
                        try: source = source + ' "%s"' % s.get_abspath()
                        except AttributeError: raise SCons.Errors.InternalError, \
                            "outdir can be a string, a node, a list of strings or nodes, or None"
            else:
                try: source = source + ' "%s"' % env['outdir'].get_abspath()
                except AttributeError: raise SCons.Errors.InternalError, \
                    "outdir can be a string, a node, a list of strings or nodes, or None"

        if env.has_key('name'):
            if SCons.Util.is_String(env['name']):
                source = source + ' "%s"' % env['name']
            else:
                raise SCons.Errors.InternalError, "name must be a string"

        if env.has_key('variant'):
            if SCons.Util.is_String(env['variant']):
                source = source + ' "%s"' % env['variant']
            elif SCons.Util.is_List(env['variant']):
                for variant in env['variant']:
                    if SCons.Util.is_String(variant):
                        source = source + ' "%s"' % variant
                    else:
                        raise SCons.Errors.InternalError, "name must be a string or a list of strings"
            else:
                raise SCons.Errors.InternalError, "variant must be a string or a list of strings"
        else:
            raise SCons.Errors.InternalError, "variant must be specified"

        for s in _DSPGenerator.srcargs:
            if env.has_key(s):
                if SCons.Util.is_String(env[s]):
                    source = source + ' "%s' % env[s]
                elif SCons.Util.is_List(env[s]):
                    for t in env[s]:
                        if SCons.Util.is_String(t):
                            source = source + ' "%s"' % t
                        else:
                            raise SCons.Errors.InternalError, s + " must be a string or a list of strings"
                else:
                    raise SCons.Errors.InternalError, s + " must be a string or a list of strings"

        source = source + ' "%s"' % str(target[0])
        source = [SCons.Node.Python.Value(source)]

    targetlist = [target[0]]
    sourcelist = source

    if env.get('auto_build_solution', 1):
        env['projects'] = targetlist
        t, s = solutionEmitter(target, target, env)
        targetlist = targetlist + t

    return (targetlist, sourcelist)

def solutionEmitter(target, source, env):
    """Sets up the DSW dependencies."""

    # todo: Not sure what sets source to what user has passed as target,
    # but this is what happens. When that is fixed, we also won't have
    # to make the user always append env['MSVSSOLUTIONSUFFIX'] to target.
    if source[0] == target[0]:
        source = []

    # make sure the suffix is correct for the version of MSVS we're running.
    (base, suff) = SCons.Util.splitext(str(target[0]))
    suff = env.subst('$MSVSSOLUTIONSUFFIX')
    target[0] = base + suff

    if not source:
        source = 'sln_inputs:'

        if env.has_key('name'):
            if SCons.Util.is_String(env['name']):
                source = source + ' "%s"' % env['name']
            else:
                raise SCons.Errors.InternalError, "name must be a string"

        if env.has_key('variant'):
            if SCons.Util.is_String(env['variant']):
                source = source + ' "%s"' % env['variant']
            elif SCons.Util.is_List(env['variant']):
                for variant in env['variant']:
                    if SCons.Util.is_String(variant):
                        source = source + ' "%s"' % variant
                    else:
                        raise SCons.Errors.InternalError, "name must be a string or a list of strings"
            else:
                raise SCons.Errors.InternalError, "variant must be a string or a list of strings"
        else:
            raise SCons.Errors.InternalError, "variant must be specified"

        if env.has_key('slnguid'):
            if SCons.Util.is_String(env['slnguid']):
                source = source + ' "%s"' % env['slnguid']
            else:
                raise SCons.Errors.InternalError, "slnguid must be a string"

        if env.has_key('projects'):
            if SCons.Util.is_String(env['projects']):
                source = source + ' "%s"' % env['projects']
            elif SCons.Util.is_List(env['projects']):
                for t in env['projects']:
                    if SCons.Util.is_String(t):
                        source = source + ' "%s"' % t

        source = source + ' "%s"' % str(target[0])
        source = [SCons.Node.Python.Value(source)]

    return ([target[0]], source)

projectAction = SCons.Action.Action(GenerateProject, None)

solutionAction = SCons.Action.Action(GenerateSolution, None)

projectBuilder = SCons.Builder.Builder(action = '$MSVSPROJECTCOM',
                                       suffix = '$MSVSPROJECTSUFFIX',
                                       emitter = projectEmitter)

solutionBuilder = SCons.Builder.Builder(action = '$MSVSSOLUTIONCOM',
                                        suffix = '$MSVSSOLUTIONSUFFIX',
                                        emitter = solutionEmitter)

default_MSVS_SConscript = None

def generate(env):
    """Add Builders and construction variables for Microsoft Visual
    Studio project files to an Environment."""

    if sys.platform == 'win32':     # otherwise we don't do anything at all
        try:
            env['BUILDERS']['MSVSProject']
        except KeyError:
            env['BUILDERS']['MSVSProject'] = projectBuilder

        try:
            env['BUILDERS']['MSVSSolution']
        except KeyError:
            env['BUILDERS']['MSVSSolution'] = solutionBuilder

        env['MSVSPROJECTCOM'] = projectAction
        env['MSVSSOLUTIONCOM'] = solutionAction

        if SCons.Script.call_stack:
            # XXX Need to find a way to abstract this; the build engine
            # shouldn't depend on anything in SCons.Script.
            env['MSVSSCONSCRIPT'] = SCons.Script.call_stack[0].sconscript
        else:
            global default_MSVS_SConscript
            if default_MSVS_SConscript is None:
                default_MSVS_SConscript = env.File('SConstruct')
            env['MSVSSCONSCRIPT'] = default_MSVS_SConscript

        # Deleted a bunch of env. variable definitions used by
        # original msvs.py to get Studio to invoke SCons
        # keep only the one for MSVSENCODING
        env['MSVSENCODING'] = 'Windows-1252'

        # Set-up ms tools paths for default version
        # merge_default_version(env)

        msvc_setup_env_once(env)

        version_num, suite = msvs_parse_version(env['MSVS_VERSION'])
        if (version_num < 7.0):
            env['MSVS']['PROJECTSUFFIX']  = '.dsp'
            env['MSVS']['SOLUTIONSUFFIX'] = '.dsw'
        else:
            env['MSVS']['PROJECTSUFFIX']  = '.vcproj'
            env['MSVS']['SOLUTIONSUFFIX'] = '.sln'

        env['GET_MSVSPROJECTSUFFIX']  = GetMSVSProjectSuffix
        env['GET_MSVSSOLUTIONSUFFIX']  = GetMSVSSolutionSuffix
        env['MSVSPROJECTSUFFIX']  = '${GET_MSVSPROJECTSUFFIX}'
        env['MSVSSOLUTIONSUFFIX']  = '${GET_MSVSSOLUTIONSUFFIX}'
        env['SCONS_HOME'] = os.environ.get('SCONS_HOME')

def exists(env):
    #if sys.platform == 'msvs' : return msvs_exists()    # for 1.2.0.d20090919
    #return detect_msvs()   # for 1.2.0.d20090223
    if sys.platform == 'win32':
        return msvc_exists()    # for 1.3.0
    else:
        return 1
    
