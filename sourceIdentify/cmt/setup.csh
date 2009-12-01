# echo "Setting sourceIdentify v2r2p3 in /home/glast/dev"

if ( $?CMTROOT == 0 ) then
  setenv CMTROOT /opt/projects/glast/tools/CMT/v1r16p20040701
endif
source ${CMTROOT}/mgr/setup.csh

set tempfile=`${CMTROOT}/mgr/cmt build temporary_name -quiet`
if $status != 0 then
  set tempfile=/tmp/cmt.$$
endif
${CMTROOT}/mgr/cmt -quiet setup -csh -pack=sourceIdentify -version=v2r2p3 -path=/home/glast/dev  $* >${tempfile}; source ${tempfile}
/bin/rm -f ${tempfile}

