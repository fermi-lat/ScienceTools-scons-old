if ( $?CMTROOT == 0 ) then
  setenv CMTROOT /afs/slac.stanford.edu/g/glast/applications/CMT/v1r16p20040701
endif
source ${CMTROOT}/mgr/setup.csh
set tempfile=`${CMTROOT}/mgr/cmt build temporary_name -quiet`
if $status != 0 then
  set tempfile=/tmp/cmt.$$
endif
${CMTROOT}/mgr/cmt -quiet cleanup -csh -pack=pgwave -version=v0r0p0 -path=/afs/slac.stanford.edu/u/gl/tosti/mywork $* >${tempfile}; source ${tempfile}
/bin/rm -f ${tempfile}

