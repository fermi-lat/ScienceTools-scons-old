CMT_tag=$(tag)
CMTROOT=/opt/projects/glast/tools/CMT/v1r16p20040701
CMT_root=/opt/projects/glast/tools/CMT/v1r16p20040701
CMTVERSION=v1r16p20040701
CMTrelease=15
cmt_hardware_query_command=uname -m
cmt_hardware=`$(cmt_hardware_query_command)`
cmt_system_version_query_command=${CMTROOT}/mgr/cmt_linux_version.sh | ${CMTROOT}/mgr/cmt_filter_version.sh
cmt_system_version=`$(cmt_system_version_query_command)`
cmt_compiler_version_query_command=${CMTROOT}/mgr/cmt_gcc_version.sh | ${CMTROOT}/mgr/cmt_filter_version.sh
cmt_compiler_version=`$(cmt_compiler_version_query_command)`
PATH=/opt/projects/glast/packages/ScienceTools-v9r1p1/InstallArea/rh9_gcc32/bin:${ROOTSYS}/bin:/opt/projects/glast/tools/CMT/v1r16p20040701/${CMTBIN}:.:/home/glast/bin:/home/glast/dev/bin:/usr/local/rsi/idl_5.4/bin:/home/glast/python/srcid:/opt/projects/glast/packages/ScienceTools-cesr/bin:/opt/projects/glast/packages/ScienceTools-LATEST/bin:/usr/local/src/fv4.4:/opt/common/lheasoft/v6.0.4/headas/i686-pc-linux-gnu-libc2.2.4/bin:/usr/local/mysql/bin:/usr/kerberos/bin:/usr/java/jre1.6.0_03/bin:/usr/local/bin:/bin:/usr/bin:/usr/X11R6/bin:/home/glast/bin
CLASSPATH=/opt/projects/glast/packages/ScienceTools-v9r1p1/InstallArea/share/bin:/opt/projects/glast/packages/ScienceTools-v9r1p1/InstallArea/share/lib:/opt/projects/glast/tools/CMT/v1r16p20040701/java
debug_option=-g
cc=gcc
cdebugflags=$(debug_option)
pp_cflags=-Di586
ccomp=$(cc) -c $(includes) $(cdebugflags) $(cflags) $(pp_cflags)
clink=$(cc) $(clinkflags) $(cdebugflags)
ppcmd=-I
preproc=c++ -MD -c 
cpp=g++
cppdebugflags=$(debug_option)
cppflags=-pipe -ansi -W -Wall  -fPIC -shared -D_GNU_SOURCE -Dlinux -Dunix  -I../src -DTRAP_FPE 
pp_cppflags=-D_GNU_SOURCE
cppcomp=$(cpp) -c $(includes) $(cppoptions) $(cppflags) $(pp_cppflags)
cpplinkflags=-Wl,-Bdynamic  $(linkdebug)
cpplink=$(cpp)   $(cpplinkflags)
for=g77
fflags=$(debug_option)
fcomp=$(for) -c $(fincludes) $(fflags) $(pp_fflags)
flink=$(for) $(flinkflags)
javacomp=javac -classpath $(src):$(CLASSPATH) 
javacopy=cp
jar=jar
X11_cflags=-I/usr/include
Xm_cflags=-I/usr/include
X_linkopts=-L/usr/X11R6/lib -lXm -lXt -lXext -lX11 -lm
lex=flex $(lexflags)
yaccflags= -l -d 
yacc=yacc $(yaccflags)
ar=ar r
ranlib=ranlib
make_shlib=${CMTROOT}/mgr/cmt_make_shlib_common.sh extract
shlibsuffix=so
shlibbuilder=g++ $(cmt_installarea_linkopts) 
shlibflags=-shared
symlink=/bin/ln -fs 
symunlink=/bin/rm -f 
build_library_links=$(cmtexe) build library_links -quiet -tag=$(tags)
remove_library_links=$(cmtexe) remove library_links -quiet -tag=$(tags)
cmtexe=${CMTROOT}/${CMTBIN}/cmt.exe
build_prototype=$(cmtexe) build prototype
build_dependencies=$(cmtexe) -quiet -tag=$(tags) build dependencies
build_triggers=$(cmtexe) build triggers
implied_library_prefix=-l
SHELL=/bin/sh
src=../src/
doc=../doc/
inc=../src/
mgr=../cmt/
application_suffix=.exe
library_prefix=lib
lock_command=chmod -R a-w ../*
unlock_command=chmod -R g+w ../*
MAKEFLAGS= --no-print-directory 
gmake_hosts=lx1 rsplus lxtest as7 dxplus ax7 hp2 aleph hp1 hpplus papou1-fe atlas
make_hosts=virgo-control1 rio0a vmpc38a
everywhere=hosts
install_command=cp 
uninstall_command=/bin/rm -f 
cmt_installarea_command=ln -s 
cmt_uninstallarea_command=/bin/rm -f 
cmt_install_area_command=$(cmt_installarea_command)
cmt_uninstall_area_command=$(cmt_uninstallarea_command)
cmt_install_action=$(CMTROOT)/mgr/cmt_install_action.sh
cmt_installdir_action=$(CMTROOT)/mgr/cmt_installdir_action.sh
cmt_uninstall_action=$(CMTROOT)/mgr/cmt_uninstall_action.sh
cmt_uninstalldir_action=$(CMTROOT)/mgr/cmt_uninstalldir_action.sh
mkdir=mkdir
cmt_installarea_prefix=InstallArea
CMT_PATH_remove_regexp=/[^/]*/
CMT_PATH_remove_share_regexp=/share/
NEWCMTCONFIG=i686-rh9-gcc32
sourceIdentify_tag=$(tag)
SOURCEIDENTIFYROOT=/home/glast/dev/sourceIdentify/v1r3p6
sourceIdentify_root=/home/glast/dev/sourceIdentify/v1r3p6
SOURCEIDENTIFYVERSION=v1r3p6
sourceIdentify_cmtpath=/home/glast/dev/
sourceIdentify_offset=home/glast/dev
sourceIdentify_project=Project1
STpolicy_tag=$(tag)
STPOLICYROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/STpolicy/v1r3
STpolicy_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/STpolicy/v1r3
STPOLICYVERSION=v1r3
STpolicy_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
STpolicy_project=Project3
GlastPolicy_tag=$(tag)
GLASTPOLICYROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/v6r14
GlastPolicy_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/v6r14
GLASTPOLICYVERSION=v6r14
GlastPolicy_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
GlastPolicy_project=Project3
GlastPatternPolicy_tag=$(tag)
GLASTPATTERNPOLICYROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/GlastPatternPolicy/v2r0
GlastPatternPolicy_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/GlastPatternPolicy/v2r0
GLASTPATTERNPOLICYVERSION=v2r0
GlastPatternPolicy_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
GlastPatternPolicy_offset=GlastPolicy
GlastPatternPolicy_project=Project3
GlastMain=${GR_APPROOT}/src/GlastMain.cxx
TestGlastMain=${GR_APPROOT}/src/TestGlastMain.cxx
GlastCppPolicy_tag=$(tag)
GLASTCPPPOLICYROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/GlastCppPolicy/v1r7p4
GlastCppPolicy_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/GlastCppPolicy/v1r7p4
GLASTCPPPOLICYVERSION=v1r7p4
GlastCppPolicy_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
GlastCppPolicy_offset=GlastPolicy
GlastCppPolicy_project=Project3
BINDIR=rh9_gcc32
cppoptions=$(cppdebugflags_s)
cppdebugflags_s=-g
cppoptimized_s=-O2 -g 
cppprofiled_s=-pg
linkdebug=-g 
makeLinkMap=-Wl,-Map,Linux.map
componentshr_linkopts=-fPIC  -ldl 
libraryshr_linkopts=-fPIC -ldl 
TMP=/tmp
hoops_tag=$(tag)
HOOPSROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/hoops/v0r4p5
hoops_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/hoops/v0r4p5
HOOPSVERSION=v0r4p5
hoops_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
hoops_project=Project3
pil_tag=$(tag)
PILROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/pil/v1r201p1
pil_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/pil/v1r201p1
PILVERSION=v1r201p1
pil_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
pil_offset=IExternal
pil_project=Project3
pil_native_version=2.0.1
pil_DIR=${GLAST_EXT}/pil/$(pil_native_version)
pil_linkopts=-L $(pil_DIR)/lib -lpil -ltermcap -lreadline
hoopsDir=${HOOPSROOT}/${BINDIR}
hoops_linkopts=-L${hoops_cmtpath}/lib -lhoops 
hoops_stamps=${HOOPSROOT}/${BINDIR}/hoops.stamp 
st_facilities_tag=$(tag)
ST_FACILITIESROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_facilities/v0r13
st_facilities_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_facilities/v0r13
ST_FACILITIESVERSION=v0r13
st_facilities_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
st_facilities_project=Project3
astro_tag=$(tag)
ASTROROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/astro/v2r14p5
astro_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/astro/v2r14p5
ASTROVERSION=v2r14p5
astro_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
astro_project=Project3
facilities_tag=$(tag)
FACILITIESROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/facilities/v2r16p22
facilities_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/facilities/v2r16p22
FACILITIESVERSION=v2r16p22
facilities_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
facilities_project=Project3
swig_tag=$(tag)
SWIGROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/swig/v0r1331p1
swig_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/swig/v0r1331p1
SWIGVERSION=v0r1331p1
swig_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
swig_offset=IExternal
swig_project=Project3
swig_native_version=1.3.31
swig_DIR=${GLAST_EXT}/swig/$(swig_native_version)
SWIG_LIB=/opt/projects/glast/extlib/swig/1.3.31/share/swig/1.3.31
LD_LIBRARY_PATH=/opt/projects/glast/packages/ScienceTools-v9r1p1/InstallArea/rh9_gcc32/lib:/opt/projects/glast/extlib/cppunit/1.10.2/lib:/opt/projects/glast/extlib/ROOT/v5.16.00-gl1/root/bin:/opt/projects/glast/extlib/ROOT/v5.16.00-gl1/root/lib:/opt/projects/glast/extlib/CLHEP/1.9.2.2/lib:/opt/projects/glast/extlib/cfitsio/v3006/lib:/opt/projects/glast/packages/ScienceTools-LATEST/lib:/opt/common/lheasoft/v6.0.4/headas/i686-pc-linux-gnu-libc2.2.4/lib:/opt/projects/glast/packages/ScienceTools-LATEST1.2126/lib/
facilities_linkopts=-L${facilities_cmtpath}/lib -lfacilities 
facilities_shlibflags=$(libraryshr_linkopts)
facilities_stamps=${FACILITIESROOT}/${BINDIR}/facilities.stamp 
PYTHONPATH=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/facilities/v2r16p22/${BINDIR}:/home/glast/python:/opt/projects/glast/packages/ScienceTools-LATEST/lib:/opt/projects/glast/packages/ScienceTools-LATEST/sane/v3r14p2/python:/opt/projects/glast/packages/ScienceTools-LATEST1.2126/lib:/opt/projects/glast/packages/ScienceTools-LATEST1.2126/facilities/v2r16p22/python
cfitsio_tag=$(tag)
CFITSIOROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/cfitsio/v1r3006
cfitsio_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/cfitsio/v1r3006
CFITSIOVERSION=v1r3006
cfitsio_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
cfitsio_offset=IExternal
cfitsio_project=Project3
ExternalLibs_tag=$(tag)
EXTERNALLIBSROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/ExternalLibs/v5r0
ExternalLibs_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/ExternalLibs/v5r0
EXTERNALLIBSVERSION=v5r0
ExternalLibs_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
ExternalLibs_offset=IExternal
ExternalLibs_project=Project3
EXTPACK_DIR=$(GLAST_EXT)
cfitsio_native_version=v3006
cfitsio_DIR=$(EXTPACK_DIR)/cfitsio/$(cfitsio_native_version)
cfitsio_libs=-L${cfitsio_DIR}/lib -lcfitsio 
cfitsio_linkopts=$(cfitsio_libs) 
CLHEP_tag=$(tag)
CLHEPROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/CLHEP/v3r0
CLHEP_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/CLHEP/v3r0
CLHEPVERSION=v3r0
CLHEP_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
CLHEP_offset=IExternal
CLHEP_project=Project3
CLHEP_native_version=1.9.2.2
CLHEP_DIR=$(GLAST_EXT)/CLHEP
CLHEPBASE=${CLHEP_DIR}/$(CLHEP_native_version)
CLHEP_linkopts=-L$(CLHEPBASE)/lib -lCLHEP
extFiles_tag=$(tag)
EXTFILESROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/extFiles/v0r7
extFiles_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/extFiles/v0r7
EXTFILESVERSION=v0r7
extFiles_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
extFiles_offset=IExternal
extFiles_project=Project3
extFiles_DIR=${GLAST_EXT}/extFiles
extFiles_native_version=v0r7
extFiles_PATH=${extFiles_DIR}/$(extFiles_native_version)
EXTFILESSYS=/opt/projects/glast/extlib/extFiles/v0r7
tip_tag=$(tag)
TIPROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/tip/v2r12
tip_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/tip/v2r12
TIPVERSION=v2r12
tip_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
tip_project=Project3
ROOT_tag=$(tag)
ROOTROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/ROOT/v5r16p1
ROOT_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/ROOT/v5r16p1
ROOTVERSION=v5r16p1
ROOT_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
ROOT_offset=IExternal
ROOT_project=Project3
ROOT_DIR=${GLAST_EXT}/ROOT
ROOT_native_version=v5.16.00-gl1
ROOT_PATH=${ROOT_DIR}/$(ROOT_native_version)/root
ROOTSYS=/opt/projects/glast/extlib/ROOT/v5.16.00-gl1/root
dict=../dict/
rootcint=rootcint
ROOT_libs=-L$(ROOT_PATH)/lib -lCore -lCint -lRIO -lNet -lTree -lMatrix -lHist -lGraf -lGpad -lPhysics -lpthread -lm -ldl -rdynamic
ROOT_GUI_libs=-L$(ROOT_PATH)/lib -lHist -lGraf -lGraf3d -lGpad -lRint -lPostscript -lTreePlayer 
ROOT_linkopts=$(ROOT_libs)
ROOT_cppflagsEx=$(ppcmd) "$(ROOT_PATH)/include" -DUSE_ROOT
ROOT_cppflags=-fpermissive
tip_linkopts=-lHist -L${tip_cmtpath}/lib -ltip 
tipDir=${TIPROOT}/${BINDIR}
tip_stamps=${TIPROOT}/${BINDIR}/tip.stamp 
astro_linkopts=-L${astro_cmtpath}/lib -lastro 
astro_stamps=${ASTROROOT}/${BINDIR}/astro.stamp 
f2c_tag=$(tag)
F2CROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/f2c/v2r2
f2c_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/f2c/v2r2
F2CVERSION=v2r2
f2c_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
f2c_project=Project3
f2c_linkopts= -lg2c 
cppunit_tag=$(tag)
CPPUNITROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/cppunit/v2r0p1
cppunit_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/IExternal/cppunit/v2r0p1
CPPUNITVERSION=v2r0p1
cppunit_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
cppunit_offset=IExternal
cppunit_project=Project3
cppunit_native_version=1.10.2
cppunit_DIR=${GLAST_EXT}/cppunit/$(cppunit_native_version)
cppunit_linkopts=-L ${cppunit_DIR}/lib/ -lcppunit -ldl 
st_facilities_linkopts=-L${st_facilities_cmtpath}/lib -lst_facilities 
st_facilities_stamps=${ST_FACILITIESROOT}/${BINDIR}/st_facilities.stamp 
source=*.cxx
STTEST=sttest
st_app_tag=$(tag)
ST_APPROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_app/v2r0p1
st_app_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_app/v2r0p1
ST_APPVERSION=v2r0p1
st_app_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
st_app_project=Project3
st_graph_tag=$(tag)
ST_GRAPHROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_graph/v1r7
st_graph_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_graph/v1r7
ST_GRAPHVERSION=v1r7
st_graph_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
st_graph_project=Project3
RootcintPolicy_tag=$(tag)
ROOTCINTPOLICYROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/RootcintPolicy/v7r0p1
RootcintPolicy_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/GlastPolicy/RootcintPolicy/v7r0p1
ROOTCINTPOLICYVERSION=v7r0p1
RootcintPolicy_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
RootcintPolicy_offset=GlastPolicy
RootcintPolicy_project=Project3
st_stream_tag=$(tag)
ST_STREAMROOT=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_stream/v0r5
st_stream_root=/opt/projects/glast/packages/ScienceTools-LATEST1.2126/st_stream/v0r5
ST_STREAMVERSION=v0r5
st_stream_cmtpath=/opt/projects/glast/packages/ScienceTools-LATEST1.2126
st_stream_project=Project3
st_streamDir=${ST_STREAMROOT}/${BINDIR}
st_stream_linkopts=-L${st_stream_cmtpath}/lib -lst_stream 
st_stream_stamps=${ST_STREAMROOT}/${BINDIR}/st_stream.stamp 
st_graph_linkopts=-L${st_graph_cmtpath}/lib -lst_graph ${st_graph_libs}
root_packages_import=-import=st_graph 
root_packages_include=$(ppcmd)"$(st_graph_root)" 
st_graph_libs=-L$(ROOT_PATH)/lib -lCore -lCint -lHist -lGraf -lGraf3d -lGpad -lTree -lRint -lPostscript -lMatrix -lPhysics -lGui -ldl 
st_appDir=${ST_APPROOT}/${BINDIR}
st_app_linkopts=-L${st_app_cmtpath}/lib -lst_app 
st_app_stamps=${ST_APPROOT}/${BINDIR}/st_app.stamp 
PFILES=/home/glast/pfiles/glast:/home/glast/pfiles;/opt/common/lheasoft/v6.0.4/headas/i686-pc-linux-gnu-libc2.2.4/syspfiles:/opt/projects/glast/packages/ScienceTools-LATEST1.2126/pfiles:/home/glast/dev//pfiles
catalogAccess_tag=$(tag)
CATALOGACCESSROOT=/home/glast/dev//catalogAccess/v0r4
catalogAccess_root=/home/glast/dev//catalogAccess/v0r4
CATALOGACCESSVERSION=v0r4
catalogAccess_cmtpath=/home/glast/dev/
catalogAccess_project=Project1
catalogAccessDir=${CATALOGACCESSROOT}/${BINDIR}
catalogAccess_linkopts=-L${catalogAccess_cmtpath}/lib -lcatalogAccess 
catalogAccess_stamps=${CATALOGACCESSROOT}/${BINDIR}/catalogAccess.stamp 
ST_apps=gtsrcid=/home/glast/dev/sourceIdentify/v1r3p6/${BINDIR}/gtsrcid.exe
GlastPatternPolicyDir=${GLASTPATTERNPOLICYROOT}/${BINDIR}
GlastPolicyDir=${GLASTPOLICYROOT}/${BINDIR}
STpolicyDir=${STPOLICYROOT}/${BINDIR}
facilitiesDir=${FACILITIESROOT}/${BINDIR}
astroDir=${ASTROROOT}/${BINDIR}
f2cDir=${F2CROOT}/${BINDIR}
st_facilitiesDir=${ST_FACILITIESROOT}/${BINDIR}
RootcintPolicyDir=${ROOTCINTPOLICYROOT}/${BINDIR}
st_graphDir=${ST_GRAPHROOT}/${BINDIR}
sourceIdentifyDir=${SOURCEIDENTIFYROOT}/${BINDIR}
tag=rh9_gcc32
package=sourceIdentify
version=v1r3p6
PACKAGE_ROOT=$(SOURCEIDENTIFYROOT)
srcdir=../src
bin=../$(sourceIdentify_tag)/
javabin=../classes/
mgrdir=cmt
project=Project1
use_requirements=requirements $(CMTROOT)/mgr/requirements $(ST_APPROOT)/cmt/requirements $(ST_GRAPHROOT)/cmt/requirements $(HOOPSROOT)/cmt/requirements $(ST_FACILITIESROOT)/cmt/requirements $(ASTROROOT)/cmt/requirements $(CATALOGACCESSROOT)/cmt/requirements $(TIPROOT)/cmt/requirements $(ST_STREAMROOT)/cmt/requirements $(STPOLICYROOT)/cmt/requirements $(FACILITIESROOT)/cmt/requirements $(F2CROOT)/cmt/requirements $(ROOTCINTPOLICYROOT)/cmt/requirements $(GLASTPOLICYROOT)/cmt/requirements $(GLASTPATTERNPOLICYROOT)/cmt/requirements $(GLASTCPPPOLICYROOT)/cmt/requirements $(PILROOT)/cmt/requirements $(SWIGROOT)/cmt/requirements $(CFITSIOROOT)/cmt/requirements $(EXTERNALLIBSROOT)/cmt/requirements $(CLHEPROOT)/cmt/requirements $(EXTFILESROOT)/cmt/requirements $(ROOTROOT)/cmt/requirements $(CPPUNITROOT)/cmt/requirements 
use_includes= $(ppcmd)"$(ST_APPROOT)" $(ppcmd)"$(ST_GRAPHROOT)" $(ppcmd)"$(HOOPSROOT)" $(ppcmd)"$(ST_FACILITIESROOT)" $(ppcmd)"$(ASTROROOT)" $(ppcmd)"$(CATALOGACCESSROOT)" $(ppcmd)"$(TIPROOT)" $(ppcmd)"$(ST_STREAMROOT)" $(ppcmd)"$(FACILITIESROOT)" $(ppcmd)"$(F2CROOT)" $(ppcmd)"$(pil_DIR)/include" $(ppcmd)"$(swig_root)/src" $(ppcmd)"${cfitsio_DIR}/include" $(ppcmd)"$(CLHEPBASE)/include" $(ppcmd)"$(ROOT_PATH)/include" $(ppcmd)"${cppunit_DIR}/include" 
use_fincludes= $(use_includes)
use_stamps= $(sourceIdentify_stamps)  $(st_app_stamps)  $(st_graph_stamps)  $(hoops_stamps)  $(st_facilities_stamps)  $(astro_stamps)  $(catalogAccess_stamps)  $(tip_stamps)  $(st_stream_stamps)  $(STpolicy_stamps)  $(facilities_stamps)  $(f2c_stamps)  $(RootcintPolicy_stamps)  $(GlastPolicy_stamps)  $(GlastPatternPolicy_stamps)  $(GlastCppPolicy_stamps)  $(pil_stamps)  $(swig_stamps)  $(cfitsio_stamps)  $(ExternalLibs_stamps)  $(CLHEP_stamps)  $(extFiles_stamps)  $(ROOT_stamps)  $(cppunit_stamps) 
use_cflags=  $(sourceIdentify_cflags)  $(st_app_cflags)  $(st_graph_cflags)  $(hoops_cflags)  $(st_facilities_cflags)  $(astro_cflags)  $(catalogAccess_cflags)  $(tip_cflags)  $(st_stream_cflags)  $(STpolicy_cflags)  $(facilities_cflags)  $(f2c_cflags)  $(RootcintPolicy_cflags)  $(GlastPolicy_cflags)  $(pil_cflags)  $(swig_cflags)  $(cfitsio_cflags)  $(ExternalLibs_cflags)  $(CLHEP_cflags)  $(ROOT_cflags)  $(cppunit_cflags) 
use_pp_cflags=  $(sourceIdentify_pp_cflags)  $(st_app_pp_cflags)  $(st_graph_pp_cflags)  $(hoops_pp_cflags)  $(st_facilities_pp_cflags)  $(astro_pp_cflags)  $(catalogAccess_pp_cflags)  $(tip_pp_cflags)  $(st_stream_pp_cflags)  $(STpolicy_pp_cflags)  $(facilities_pp_cflags)  $(f2c_pp_cflags)  $(RootcintPolicy_pp_cflags)  $(GlastPolicy_pp_cflags)  $(pil_pp_cflags)  $(swig_pp_cflags)  $(cfitsio_pp_cflags)  $(ExternalLibs_pp_cflags)  $(CLHEP_pp_cflags)  $(ROOT_pp_cflags)  $(cppunit_pp_cflags) 
use_cppflags=  $(sourceIdentify_cppflags)  $(st_app_cppflags)  $(st_graph_cppflags)  $(hoops_cppflags)  $(st_facilities_cppflags)  $(astro_cppflags)  $(catalogAccess_cppflags)  $(tip_cppflags)  $(st_stream_cppflags)  $(STpolicy_cppflags)  $(facilities_cppflags)  $(f2c_cppflags)  $(RootcintPolicy_cppflags)  $(GlastPolicy_cppflags)  $(pil_cppflags)  $(swig_cppflags)  $(cfitsio_cppflags)  $(ExternalLibs_cppflags)  $(CLHEP_cppflags)  $(ROOT_cppflags)  $(cppunit_cppflags) 
use_pp_cppflags=  $(sourceIdentify_pp_cppflags)  $(st_app_pp_cppflags)  $(st_graph_pp_cppflags)  $(hoops_pp_cppflags)  $(st_facilities_pp_cppflags)  $(astro_pp_cppflags)  $(catalogAccess_pp_cppflags)  $(tip_pp_cppflags)  $(st_stream_pp_cppflags)  $(STpolicy_pp_cppflags)  $(facilities_pp_cppflags)  $(f2c_pp_cppflags)  $(RootcintPolicy_pp_cppflags)  $(GlastPolicy_pp_cppflags)  $(pil_pp_cppflags)  $(swig_pp_cppflags)  $(cfitsio_pp_cppflags)  $(ExternalLibs_pp_cppflags)  $(CLHEP_pp_cppflags)  $(ROOT_pp_cppflags)  $(cppunit_pp_cppflags) 
use_fflags=  $(sourceIdentify_fflags)  $(st_app_fflags)  $(st_graph_fflags)  $(hoops_fflags)  $(st_facilities_fflags)  $(astro_fflags)  $(catalogAccess_fflags)  $(tip_fflags)  $(st_stream_fflags)  $(STpolicy_fflags)  $(facilities_fflags)  $(f2c_fflags)  $(RootcintPolicy_fflags)  $(GlastPolicy_fflags)  $(pil_fflags)  $(swig_fflags)  $(cfitsio_fflags)  $(ExternalLibs_fflags)  $(CLHEP_fflags)  $(ROOT_fflags)  $(cppunit_fflags) 
use_pp_fflags=  $(sourceIdentify_pp_fflags)  $(st_app_pp_fflags)  $(st_graph_pp_fflags)  $(hoops_pp_fflags)  $(st_facilities_pp_fflags)  $(astro_pp_fflags)  $(catalogAccess_pp_fflags)  $(tip_pp_fflags)  $(st_stream_pp_fflags)  $(STpolicy_pp_fflags)  $(facilities_pp_fflags)  $(f2c_pp_fflags)  $(RootcintPolicy_pp_fflags)  $(GlastPolicy_pp_fflags)  $(pil_pp_fflags)  $(swig_pp_fflags)  $(cfitsio_pp_fflags)  $(ExternalLibs_pp_fflags)  $(CLHEP_pp_fflags)  $(ROOT_pp_fflags)  $(cppunit_pp_fflags) 
use_linkopts= $(cmt_installarea_linkopts)   $(sourceIdentify_linkopts)  $(st_app_linkopts)  $(st_graph_linkopts)  $(hoops_linkopts)  $(st_facilities_linkopts)  $(astro_linkopts)  $(catalogAccess_linkopts)  $(tip_linkopts)  $(st_stream_linkopts)  $(STpolicy_linkopts)  $(facilities_linkopts)  $(f2c_linkopts)  $(RootcintPolicy_linkopts)  $(GlastPolicy_linkopts)  $(pil_linkopts)  $(swig_linkopts)  $(cfitsio_linkopts)  $(ExternalLibs_linkopts)  $(CLHEP_linkopts)  $(ROOT_linkopts)  $(cppunit_linkopts) 
use_libraries= $(st_app_libraries)  $(st_graph_libraries)  $(hoops_libraries)  $(st_facilities_libraries)  $(astro_libraries)  $(catalogAccess_libraries)  $(tip_libraries)  $(st_stream_libraries)  $(STpolicy_libraries)  $(facilities_libraries)  $(f2c_libraries)  $(RootcintPolicy_libraries)  $(GlastPolicy_libraries)  $(GlastPatternPolicy_libraries)  $(GlastCppPolicy_libraries)  $(pil_libraries)  $(swig_libraries)  $(cfitsio_libraries)  $(ExternalLibs_libraries)  $(CLHEP_libraries)  $(extFiles_libraries)  $(ROOT_libraries)  $(cppunit_libraries) 
includes= $(use_includes)
fincludes= $(includes)
gtsrcid_use_linkopts=  $(sourceIdentify_linkopts)  $(st_app_linkopts)  $(st_graph_linkopts)  $(hoops_linkopts)  $(st_facilities_linkopts)  $(astro_linkopts)  $(catalogAccess_linkopts)  $(tip_linkopts)  $(st_stream_linkopts)  $(STpolicy_linkopts)  $(facilities_linkopts)  $(f2c_linkopts)  $(RootcintPolicy_linkopts)  $(GlastPolicy_linkopts)  $(pil_linkopts)  $(swig_linkopts)  $(cfitsio_linkopts)  $(ExternalLibs_linkopts)  $(CLHEP_linkopts)  $(ROOT_linkopts)  $(cppunit_linkopts) 
constituents= pfiles gtsrcid 
all_constituents= $(constituents)
constituentsclean= gtsrcidclean pfilesclean 
all_constituentsclean= $(constituentsclean)
cmt_installarea_paths=$(cmt_installarea_prefix)/$(tag)/bin $(cmt_installarea_prefix)/$(tag)/lib $(cmt_installarea_prefix)/share/lib $(cmt_installarea_prefix)/share/bin
Project4_installarea_prefix=$(cmt_installarea_prefix)
Project4_installarea_prefix_remove=$(Project4_installarea_prefix)
cmt_installarea_linkopts= -L/opt/projects/glast/packages/ScienceTools-v9r1p1/$(Project4_installarea_prefix)/$(tag)/lib 
