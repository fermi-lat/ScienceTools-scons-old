//Author: Vlasios Vasileiou <vlasisva@gmail.com>
// $Header$
#include "BackgroundEstimator/BackgroundEstimator.h"

#define DEBUG

ClassImp(BackgroundEstimator)

BackgroundEstimator::~BackgroundEstimator() 
{//do some cleanup
 if(fResidualOverExposure) fResidualOverExposure->Close();
 if(fRateFit)              fRateFit->Close();
 if(fThetaPhiFits)         fThetaPhiFits->Close();
 if(fCorrectionFactors)    fCorrectionFactors->Close();
}


//BackgroundEstimator::BackgroundEstimator():
//fResidualOverExposure(0),fRateFit(0),fThetaPhiFits(0),fCorrectionFactors(0){};

BackgroundEstimator::BackgroundEstimator(string aClass, double EMin, double EMax, int EBins, float ZTheta_Cut,  bool initialize, bool ShowLogo):
Energy_Min_datafiles(0),Energy_Max_datafiles(0),Energy_Bins_datafiles(0),
Energy_Min_user(EMin),Energy_Max_user(EMax),Energy_Bins_user(EBins),FT1ZenithTheta_Cut(ZTheta_Cut),UsingDefaultBinning(true),
DataClass(aClass),EstimatorVersion(1.40),Residuals_version(1.3),RateFit_version(1.3),ThetaPhiFits_version(1.3),
StartTime(0),EndTime(0),StopTime(0),TimeBins(0),BinSize(0.5),fResidualOverExposure(0),fRateFit(0),fThetaPhiFits(0),fCorrectionFactors(0)
{
 if (ShowLogo) {
   printf("*----------------------------------------------*\n");
   printf("|               Background Estimator           |\n");
   printf("|                 v%.2f 25/Apr/2011            |\n",EstimatorVersion);
   printf("|                                              |\n");
   printf("| contact:     Vlasios Vasileiou               |\n");
   printf("|              vlasios.vasileiou@lupm.in2p3.fr |\n");
   printf("| http://confluence.slac.stanford.edu/x/ApIeAg |\n");
   printf("*----------------------------------------------*\n");
 }

  L_BINS = 720;
  B_BINS = 360;
  vector <string> VALID_CLASSES;
  VALID_CLASSES.push_back("P6_V3_TRANSIENT::FRONT");
  VALID_CLASSES.push_back("P6_V3_TRANSIENT::BACK");
  VALID_CLASSES.push_back("P6_V3_TRANSIENT");
  VALID_CLASSES.push_back("P6_V3_DIFFUSE::FRONT");
  VALID_CLASSES.push_back("P6_V3_DIFFUSE::BACK");
  VALID_CLASSES.push_back("P6_V3_DIFFUSE");
  VALID_CLASSES.push_back("P7TRANSIENT_V6");
  VALID_CLASSES.push_back("P7TRANSIENT_V6::FRONT");
  VALID_CLASSES.push_back("P7TRANSIENT_V6::BACK");

  bool goodClass=false;
  for (unsigned int i=0;i<VALID_CLASSES.size();i++) {
     if (DataClass==VALID_CLASSES[i]) {goodClass=true; break;}
  }

  if (!goodClass) {
      printf("%s: Only \n",__FUNCTION__);
      for (unsigned int i=0;i<VALID_CLASSES.size();i++) printf(" %s",VALID_CLASSES[i].c_str());
      printf(" classes are supported\n");
      return;
  }

  if (ShowLogo) printf("%s: Using %s data class.\n",__FUNCTION__,DataClass.c_str());
  DataClassName_noConv=TOOLS::GetDataClassName_noConv(DataClass);
  ConversionName      =TOOLS::GetConversionName(DataClass);
  ConversionType      =TOOLS::GetConversionType(DataClass);
  DataClassVersion    =TOOLS::GetDataClassVersion(DataClass);
  MinCTBClassLevel    =TOOLS::GetCTBClassLevel(DataClass);
  DataDir             =TOOLS::GetS("BASEDIR")+"/gtgrb_data/Bkg_Estimator/";

  if (initialize) { //normal operation
      string astring;
      astring=DataDir+"Residual_Over_Exposure_"+DataClass+".root";
      fResidualOverExposure = TFile::Open(astring.c_str());
      if (!fResidualOverExposure) {printf("%s: Data file %s cannot be read. Did you get the data files?\n",__FUNCTION__,astring.c_str()); exit(1);}

      sscanf(fResidualOverExposure->Get("Energy_Data")->GetTitle(),"%lf-%lf-%d",&Energy_Min_datafiles,&Energy_Max_datafiles,&Energy_Bins_datafiles);

      if (Energy_Min_user<=0)  Energy_Min_user=Energy_Min_datafiles;
      else if (fabs(Energy_Min_user-Energy_Min_datafiles)>0.1) UsingDefaultBinning=false;
      if (Energy_Max_user<=0)  Energy_Max_user=Energy_Max_datafiles;
      else if (fabs(Energy_Max_user-Energy_Max_datafiles)>0.1) UsingDefaultBinning=false;
      if (Energy_Bins_user<=0) Energy_Bins_user=Energy_Bins_datafiles;
      else if (Energy_Bins_user!=Energy_Bins_datafiles) UsingDefaultBinning=false;

      if (ShowLogo) {
                                  printf("Data Files Energy: (%.1f-%.1f)MeV - %d bins\n",Energy_Min_datafiles,Energy_Max_datafiles,Energy_Bins_datafiles);
         if (UsingDefaultBinning) printf("User is using the above energy configuration\n");
   	 else                     printf("User's Energy:     (%.1f-%.1f)MeV - %d bins\n",Energy_Min_user,Energy_Max_user,Energy_Bins_user);
      }
      
      float FT1ZenithTheta_Cut_datafiles;
      sscanf(fResidualOverExposure->Get("FT1ZenithTheta_Cut")->GetTitle(),"%f",&FT1ZenithTheta_Cut_datafiles);
      if (FT1ZenithTheta_Cut<=0) FT1ZenithTheta_Cut=FT1ZenithTheta_Cut_datafiles;
      else if (fabs(FT1ZenithTheta_Cut-FT1ZenithTheta_Cut_datafiles)>0.1) {
          printf("%s: WARNING: You are overriding the default FT1ZenithTheta_Cut (%.1fdeg). New value is %.0fdeg. Note: BKG Estimates do not include albedos.\n", __FUNCTION__,FT1ZenithTheta_Cut_datafiles,FT1ZenithTheta_Cut);
	  UsingDefaultBinning=false;
      }	     

      if (ShowLogo) printf("Data Files FT1ZenithTheta_Cut: %.1fdeg\n",FT1ZenithTheta_Cut);
      
      float aversion=atof(fResidualOverExposure->Get("version")->GetTitle());
      if (aversion<Residuals_version) {
           printf("%s: Warning! You are using a Residuals data file that has an older version than the latest (v%.2f) one.\n",__FUNCTION__,Residuals_version);
           Residuals_version = aversion;
      }

      astring = DataDir+"RateFit_"+DataClassName_noConv+"_"+ConversionName+".root";
      fRateFit = TFile::Open(astring.c_str());
      if (!fRateFit) {printf("%s: Data file %s cannot be read. Did you get the data files?\n",__FUNCTION__,astring.c_str()); exit(1);}

      aversion=atof(fRateFit->Get("version")->GetTitle());
      if (aversion<RateFit_version) {
           printf("%s: Warning! You are using a RateFit data file that has an older version than the latest (v%.2f) one.\n",__FUNCTION__,RateFit_version);
           RateFit_version = aversion;
      }
      fRateFit->Close();

      astring=DataDir+"ThetaPhi_Fits_"+DataClassName_noConv.c_str()+"_"+ConversionName+".root";
      fThetaPhiFits = TFile::Open(astring.c_str());
      if (!fThetaPhiFits) {printf("%s: Data file %s cannot be read. Did you get the data files?\n",__FUNCTION__,astring.c_str()); exit(1);}
      aversion=atof(fThetaPhiFits->Get("version")->GetTitle());
      if (aversion<RateFit_version) {
           printf("%s: Warning! You are using a ThetaPhiFits data file that has an older version than the latest (v%.2f) one.\n",__FUNCTION__,RateFit_version);
           ThetaPhiFits_version = aversion;
      }
      fThetaPhiFits->Close();


      //Read Correction factors
      sprintf(name,"%s/TimeCorrectionFactor_%s_%s.root",DataDir.c_str(),DataClassName_noConv.c_str(),ConversionName.c_str());
      fCorrectionFactors= TFile::Open(name);
      if (!fCorrectionFactors) {printf("%s: Can't open file %s\n",__FUNCTION__,name); exit(1);}
      
      for (int iE=0;iE<=Energy_Bins_datafiles;iE++) {
          sprintf(name,"hCorrectionFactor_%d",iE);
          RatiovsTime.push_back((TH1F*)fCorrectionFactors->Get(name));
      }
   }
   else {
   }
}


//#define DEBUG

void BackgroundEstimator::CreateDataFiles(string FitsAllSkyFilesList, string FT2_FILE){

  TimeStep=1.0; //don't change that - left for debugging purposes
  Energy_Min_datafiles=Energy_Min_user;
  Energy_Max_datafiles=Energy_Max_user;
  Energy_Bins_datafiles=Energy_Bins_user;

  printf("%s: ZenithTheta Cut=%.1f deg, BinSize=%.1f deg\n",__FUNCTION__,FT1ZenithTheta_Cut,BinSize);
  printf("%s: Energy Range = (%.1e, %.1e)MeV, Energy_Bins=%d\n",__FUNCTION__,Energy_Min_datafiles,Energy_Max_datafiles,Energy_Bins_datafiles);

  //Read starting and ending time of the data in the FT1 Fits Files
  fitsfile *fptr;
  int status = 0;	
  long nrows;
  int hdutype,res,anynul;
  FILE * ftemp;
  //1. PREPARE FILES
  char buffer[1024];
  FILE * fOldFitsList = fopen(FitsAllSkyFilesList.c_str(),"r");
  if (!fOldFitsList) {printf("%s: file %s cannot be read.\n",__FUNCTION__,FitsAllSkyFilesList.c_str()); return;}

  //2.READ TIMES FROM GENERATED FILES    
  ftemp = fopen(FitsAllSkyFilesList.c_str(),"r");
  res=fscanf(ftemp,"%s",name);
  status=0;
  fits_open_file(&fptr, name, READONLY, &status);
  if (status) fits_report_error(stderr, status);  status=0;
  fits_movabs_hdu(fptr, 2, &hdutype, &status);
  if (status) fits_report_error(stderr, status);  status=0;
  fits_read_col (fptr,TDOUBLE,10,1, 1, 1, NULL,&StartTime, &anynul, &status);
  if (status) fits_report_error(stderr, status);  status=0;
  fits_close_file(fptr, &status);

  char aname2[2000];
  while (fscanf(ftemp,"%s",aname2)==1) sprintf(name,"%s",aname2);
  status=0;
  fits_open_file(&fptr, name, READONLY, &status);
  if (status) fits_report_error(stderr, status);
  fits_movabs_hdu(fptr, 2, &hdutype, &status);
  if (status) fits_report_error(stderr, status);  status=0;
  fits_get_num_rows(fptr, &nrows, &status);
  if (status) fits_report_error(stderr, status);  status=0;
  fits_read_col (fptr,TDOUBLE,10,nrows, 1, 1, NULL,&EndTime, &anynul, &status);
  fits_close_file(fptr, &status);
  fclose (ftemp);

  printf("FT1 StartTime-EndTime %f %f\n",StartTime,EndTime);
  if (StartTime==EndTime) {printf("%s:StartTime==EndTime?? \n",__FUNCTION__); exit(1);} //this also includes when they are both zero

  TimeBins = int((EndTime-StartTime)/TimeStep);
  StopTime = StartTime + TimeStep*TimeBins;
  printf("%s: Using MET:(%f-%f), dt=%e sec from all-sky file\n",__FUNCTION__,StartTime,StopTime,StopTime-StartTime);


  //3. MAKE PLOTS
  sprintf(name,"%s/Plots_%s.root",DataDir.c_str(),DataClass.c_str());
  ftemp = fopen(name,"r");
  if (!ftemp) {
       printf("%s: Making plots...\n",__FUNCTION__);
       double midtime=(StopTime+StartTime)/2;
       TOOLS::Make_Plots(midtime-StartTime,StopTime-midtime,midtime,name,FT2_FILE);
  }
  else  fclose(ftemp);

  //4. MAKE THETA/PHI DISTRIBUTIONS
  sprintf(name,"%s/ThetaPhi_Fits_%s_%s.root",DataDir.c_str(),DataClassName_noConv.c_str(),ConversionName.c_str());
  ftemp = fopen(name,"r"); 
  if (!ftemp) { 
    printf("%s: Making Theta & Phi fits...\n",__FUNCTION__); 
    Make_ThetaPhi_Fits(FitsAllSkyFilesList); 
  } 
  else fclose(ftemp);

  //5. MAKE RATE FITS
  sprintf(name,"%s/RateFit_%s_%s.root",DataDir.c_str(),DataClassName_noConv.c_str(),ConversionName.c_str());
  ftemp = fopen(name,"r"); 
  if (!ftemp) { 
    printf("%s: Making Rate fit...\n",__FUNCTION__);
    Make_McIlwainL_Fits(FitsAllSkyFilesList); 
  } 
  else fclose(ftemp); 

  if (DataClass!="LLE") {
      //3. RESIDUAL_OVER_EXPOSURE
       sprintf(name,"%s/Residual_Over_Exposure_%s.root",DataDir.c_str(),DataClass.c_str());
       ftemp = fopen(name,"r"); 
       if (!ftemp) {
          //////////////////////////////////////////
          //5.1.Exposure
             sprintf(name,"%s/ltCube_%s.fits",DataDir.c_str(),DataClass.c_str());
                  ftemp=fopen(name,"r"); 
             if (!ftemp) {
                sprintf(buffer,"gtltcube scfile=%s evfile=@%s outfile=%s dcostheta=0.025 binsz=1 zmax=%f clobber=yes phibins=10 2>&1",FT2_FILE.c_str(),FitsAllSkyFilesList.c_str(),name,FT1ZenithTheta_Cut);
                #ifdef DEBUG
                FILE *pipe = popen(buffer, "r");
                printf("%s: Executing command: %s\n",__FUNCTION__,buffer);    
                while (fgets(buffer,sizeof(buffer),pipe))  printf("	|%s",buffer);
                pclose(pipe);
                #else 
                sprintf(buffer,"%s >/dev/null",buffer);
                system(buffer);
                #endif
              } 
              else fclose(ftemp);
     
     
           //////////////////////////////////////////
           //5.2.Residual
           sprintf(name,"%s/Residual_%s.root",DataDir.c_str(),DataClass.c_str());
           ftemp = fopen(name,"r"); 
           if (!ftemp) { 
              printf("%s: Calculating Residuals...\n",__FUNCTION__); fflush(stdout); 
              CalcResiduals(FitsAllSkyFilesList);
           } 
           else fclose(ftemp); 
          
           //5.3. Calculate exposure maps
           sprintf(name,"%s/exposure_%s.fits",DataDir.c_str(),DataClass.c_str());
           ftemp = fopen(name,"r"); 
           if (!ftemp) { 
                printf("%s: Creating exposure map %s...\n",__FUNCTION__,name); 
                sprintf(buffer,"gtexpcube infile=%s/ltCube_%s.fits evfile=@%s cmfile=NONE outfile=%s irfs=%s nxpix=1 nypix=1 pixscale=1 coordsys=GAL xref=0 yref=0 axisrot=0 proj=CAR emin=%f emax=%f enumbins=%d bincalc=CENTER clobber=yes 2>&1",DataDir.c_str(),DataClass.c_str(),FitsAllSkyFilesList.c_str(),name,DataClass.c_str(),Energy_Min_datafiles,Energy_Max_datafiles,Energy_Bins_datafiles);
     
                #ifdef DEBUG
                FILE *pipe = popen(buffer, "r");
                printf("%s: Executing command: %s\n",__FUNCTION__,buffer);
                while (fgets(buffer,sizeof(buffer),pipe))  printf("	|%s",buffer);
                pclose(pipe);
                #else 
                sprintf(buffer,"%s 1>/dev/null",buffer);
                system(buffer);
                #endif
          } 
          else fclose(ftemp); 
     
     
          ///////////////////////////////////////////
          //5.4. Calculate Residual Over Exposure
          TH2F * hExposureAllSky = new TH2F("hExposureAllSky","hExposureAllSky",L_BINS,-180,180,B_BINS,-90,90);
          sprintf(name,"%s/Residual_%s.root",DataDir.c_str(),DataClass.c_str()); 
          TFile * fResidual = TFile::Open(name);
          sprintf(name,"%s/Residual_Over_Exposure_%s.root",DataDir.c_str(),DataClass.c_str()); 
          TFile * fExposure = new TFile(name,"RECREATE");
     
          TH2D*  hSolidAngle = new TH2D("hSolidAngle","hSolidAngle",L_BINS,-180,180,B_BINS,-90,90); 
          double thetaphi=BinSize*DEG_TO_RAD; 
          double theta1,theta2,binarea; 
          for (int j=1;j<=B_BINS;j++) { 
             for (int i=1;i<=L_BINS;i++) { 
                theta1=(90+hSolidAngle->GetYaxis()->GetBinLowEdge(j))*DEG_TO_RAD; 
                theta2=(90+hSolidAngle->GetYaxis()->GetBinUpEdge(j))*DEG_TO_RAD; 
                binarea = (cos(theta1)-cos(theta2))*thetaphi; 
                hSolidAngle->SetBinContent(i,j,binarea); 
             } 
          }   
          hSolidAngle->Write(); 
      
          for (short unsigned int ie=1;ie<=Energy_Bins_datafiles;ie++) {
             sprintf(name,"hResidual_%d;1",ie); 
             TH2F * haResidual = (TH2F*)fResidual->Get(name);
             sprintf(name,"hResidual_Over_Exposure_%d",ie);
             TH2F *haResidualOverExposure = (TH2F*)haResidual->Clone(name);
             haResidualOverExposure->SetTitle("hResidual_Over_Exposure");
             haResidual->Delete();
     
             sprintf(name,"%s/exposure_%s.fits",DataDir.c_str(),DataClass.c_str());
             TOOLS::ReadExposureMap(name,hExposureAllSky,ie,1);
     
             sprintf(name,"hExposureAllSky_%d",ie);
             //hExposureAllSky->Write(name);
             haResidualOverExposure->Divide(hSolidAngle);
             haResidualOverExposure->Divide(hExposureAllSky);
     
             sprintf(name,"hResidual_Over_Exposure_%d",ie);
             haResidualOverExposure->Write(name);
             haResidualOverExposure->Delete();
     
             TOOLS::ProgressBar(ie-1,Energy_Bins_datafiles);
          }
          hExposureAllSky->Delete();
          fResidual->Close();

          sprintf(name,"%e_%e_%d",Energy_Min_datafiles,Energy_Max_datafiles,Energy_Bins_datafiles);
          TNamed Data = TNamed("Energy_Data",name);
          fExposure->cd(); Data.Write(); 

          sprintf(name,"%f",FT1ZenithTheta_Cut);
          Data = TNamed("FT1ZenithTheta_Cut",name);
          Data.Write(); 

          sprintf(name,"%.2f",Residuals_version);
          Data = TNamed("version",name);
          Data.Write();

          fExposure->Close();
       }
       else  fclose(ftemp);
    }


};


unsigned short int BackgroundEstimator::Energy2Bin(float Energy){
  static const double dlEnergy = (log10(Energy_Max_datafiles)-log10(Energy_Min_datafiles))/Energy_Bins_datafiles;
  static const double lEnergy_Min = log10(Energy_Min_datafiles);

  if      (Energy<Energy_Min_datafiles) return 0;
  else if (Energy>=Energy_Max_datafiles) return Energy_Bins_datafiles+1;
  else return 1+(int)(floor((log10(Energy)-lEnergy_Min)/dlEnergy));
};


float BackgroundEstimator::Bin2Energy(unsigned short int bin){
  static const double dlEnergy = (log10(Energy_Max_datafiles)-log10(Energy_Min_datafiles))/Energy_Bins_datafiles;
  static const double lEnergy_Min = log10(Energy_Min_datafiles);
  if (bin==0) return Energy_Min_datafiles;
  else if (bin==Energy_Bins_datafiles+1) return Energy_Max_datafiles;
  else return pow(10,lEnergy_Min+(bin+0.5)*dlEnergy);
};


bool BackgroundEstimator::PassesCuts(fitsfile * fptr, long int i, int format) {
  int status=0,anynul;
  if (format==DATA_FORMAT_P7)  {
      static int EventClass=0;
      fits_read_col (fptr,TINT,15,i, 1, 1, NULL,&EventClass, &anynul, &status);
      if (!EventClassMask&EventClass) return false;
  }
  else {
    static int CTBClassLevel=0;
    if      (format==DATA_FORMAT_P6_OLD) fits_read_col (fptr,TINT,18,i, 1, 1, NULL,&CTBClassLevel, &anynul, &status);
    else if (format==DATA_FORMAT_P6_NEW) fits_read_col (fptr,TINT,15,i, 1, 1, NULL,&CTBClassLevel, &anynul, &status);
    else {printf("%s: what is going on?\n",__FUNCTION__); exit(1);}
    if   (CTBClassLevel<MinCTBClassLevel) return false; //apply class cut
  }
  //printf("ctb %d %d\n",CTBClassLevel,MinCTBClassLevel);


  if (ConversionType!=-1) { //if !BOTH
      static int aConversionType=0;
      fits_read_col (fptr,TINT,16,i, 1, 1, NULL,&aConversionType, &anynul, &status);
      //printf("conv %d %d\n",ConversionType,aConversionType);
      if (aConversionType!=ConversionType) return false; //apply Conversion Type front/back
  }

  static double FT1Energy=0;
  fits_read_col (fptr,TDOUBLE,1,i, 1, 1, NULL,&FT1Energy, &anynul, &status);
  //printf("energy %f %f %f\n",FT1Energy,Energy_Min,Energy_Max_datafiles);
  if (FT1Energy<Energy_Min_datafiles || FT1Energy>Energy_Max_datafiles) return false; //energy cut

  static double FT1ZenithTheta=0;
  fits_read_col (fptr,TDOUBLE,8,i, 1, 1, NULL,&FT1ZenithTheta, &anynul, &status);
  //printf("zt %f %f\n",FT1ZenithTheta,FT1ZenithTheta_Cut);
  if (FT1ZenithTheta>FT1ZenithTheta_Cut) return false; //ZTheta cut

  return true;
}

double BackgroundEstimator::GimmeCorrectionFactor(short int ie, double MET) {
  if (RatiovsTime[ie]==NULL) return 1;
  if (ie<=0 || ie>Energy_Bins_datafiles) {printf("%s: energy bin that is out of bounds %d submitted\n",__FUNCTION__,ie); return 1;}
  double CorrectionCoeff = RatiovsTime[ie]->GetBinContent(RatiovsTime[ie]->FindBin(MET));
  //printf("met=%f bin=%d cor=%f\n",MET,RatiovsTime[ie]->FindBin(MET),RatiovsTime[ie]->GetBinContent(RatiovsTime[ie]->FindBin(MET)));
  if (CorrectionCoeff==0) return 1;

  return 1./CorrectionCoeff; //CorrectionCoeff = 1/ratio. (ratio=bkg/sig)
}

