/*!\class GRBTest.cxx
 * \brief Test class for GRB simulation studies.
 * 
 * This class is called from GRB Gaudi Algorithm.
 * It basically compute the spectrum and returns a photons for the montecarlo.
 * It calls the GRBSim class as kernel of the simulation.
 * Some quantities are also calculated to help people understanding 
 * GRB physics.
 *
 */

// Include files
#include "FluxSvc/IFluxSvc.h"
#include "FluxSvc/IFlux.h"

// GlastEvent for creating the McEvent stuff
#include "Event/TopLevel/Event.h"
#include "Event/TopLevel/MCEvent.h"
#include "Event/MonteCarlo/McParticle.h"
#include "Event/TopLevel/EventModel.h"

// Gaudi system includes

#include "GaudiKernel/IDataProviderSvc.h"
#include "GaudiKernel/SmartDataPtr.h"
#include "GaudiKernel/IParticlePropertySvc.h"
#include "GaudiKernel/SmartRefVector.h"
#include "GaudiKernel/MsgStream.h"
#include "GaudiKernel/AlgFactory.h"
#include "GaudiKernel/Algorithm.h"
#include "facilities/Util.h"
#include <list>
#include <string>
#include <vector>
//#include "GaudiKernel/ParticleProperty.h"


// GRB includes
#include "../GRB/GRBSpectrum.h"
//include files for ROOT...
#include "TTree.h"
#include "TBranch.h"
#include "TObjArray.h"
#include "TFile.h"

using namespace std;

class GRBTest{
    
public:
  //! Constructor
  GRBTest();
  ~GRBTest(){}
  //! Return the pointer to flux service
  inline void setService(IFluxSvc* ptr){m_fsvc = ptr;}
  //! Calculate the fluence in the energy band between e1 and e2.
  double CalculateFluence(double ee/* MeV */,
			  double e1=cst::enmin*1e-6/* MeV */,
			  double e2=cst::enmax*1e-6/* MeV */);
  //! Generate a GRB
  int Start(std::vector<char*> argv);
  //! Help printout utility
  void help();
  //! List all the sources available
  void listSources(const std::list<std::string>& source_list );
  //! List of loaded spectrum objects
  void listSpectra();
  
private:  
  IFlux* m_flux;    // pointer the a flux object
  IFluxSvc* m_fsvc; // pointer to the flux Service 
  
  char *m_source_name;
  bool savef;
  double TIME;
  int EVENTS;
  const char * default_arg;//="GRBSpectrum";
};


GRBTest::GRBTest()
{
  cout<<" Starting a new Test"<<endl;
}
//------------------------------------------------------------------------------
double GRBTest::CalculateFluence(double ee/* MeV */,
				 double e1/*=cst::enmin*1e-6 MeV */,
				 double e2/*=cst::enmax*1e-6 MeV */)
{
  double fluence;
  if (ee>=e1 && ee<=e2) 
    {
      fluence=ee;
    }
  else 
    {
      fluence=0.0;
    }
  return fluence;
}

//------------------------------------------------------------------------------
void GRBTest::help() {
  std::cout << 
    "   Simple test program for Transient Sources.\n"
    "   Command line args are \n"
    "      '-events <number of events to create>'\n"
    "      '-time <time in seconds>'    for the maximum time\n"
    "      '-list' lists the available spectra\n"
    "      '-save' <name of the source> to save the events in a ROOT tree"
    "      '-help' for this help"
	    << std::endl;
}

//------------------------------------------------------------------------------
void GRBTest::listSources(const std::list<std::string>& source_list ) {
   std::cout << "List of available sources:" << std::endl;
   for( std::list<std::string>::const_iterator it = source_list.begin(); 
   it != source_list.end(); ++it) { 
      std::cout << '\t'<< *it << std::endl;
   }
}

//------------------------------------------------------------------------------
void GRBTest::listSpectra() {
  std::cout << "List of loaded Spectrum objects: " << std::endl;
  std::list<std::string> spectra(m_fsvc->fluxNames());
  for( std::list<std::string>::const_iterator it = spectra.begin(); 
       it != spectra.end(); ++it) { 
    std::cout << '\t'<< *it << std::endl;
  }
}

//------------------------------------------------------------------------------

int GRBTest::Start(std::vector<char*> argv)
{
  int argc = argv.size();
  //  cout<<argc<<endl;
  int nume,i;
  double dt;
  int num_sources=0;
  double time_max=TIME;  //time to use for flux and rate functions
  int events_max=EVENTS;
  double time,energy,Rate,Area;
  // Vector dir;
  HepVector3D dir;

  double cos_theta,phi;
  int current_arg = 1;
  double fluence1,fluence2,fluence3,fluence4,fluence5;
  default_arg="GRBSpectrum";
  std::string arg_name(default_arg);
  vector<std::string> sources;
  /*
    cout << "------------------------------------------------------" <<endl;
    cout << " Flux test program: type 'GRBTest.exe -help' for help" <<endl;
    cout << ( ( argc == 1)?  " No command line args, using defaults"
    :  "") <<endl;
  */
  savef=false;
  while(current_arg < argc)
    {
      arg_name = argv[current_arg];
      if("-help" == arg_name || "help" == arg_name) 
	{ 
	  help();
	  return 0;
	}
      
      else if("-list" == arg_name) 
	{ 
	  listSources(m_fsvc->fluxNames());
	  listSpectra(); 
         return 0; 
      }

      else if("-time" == arg_name) {
	time_max =atof(argv[++current_arg]);
	//cout<<" MAX TIME = "<<time_max<<endl;
      }
      else if("-events" == arg_name) {
	events_max = atoi(argv[++current_arg]);
	//cout<<" MAX NUM OF EVENTS = "<<events_max<<endl;
	if (events_max<1) return 0;
      }
      else if("-save" == arg_name) {
	savef=true;
	m_source_name = argv[++current_arg];
      }
      else if('-' == arg_name[0]) {
	std::cerr << "Unrecognized option "<< arg_name << ", -help for help" << std::endl;}
      else
	{
	  sources.push_back(arg_name);
	  num_sources++;
	}
      current_arg++;
   }
  if(0 == sources.size())
    {
      sources.push_back(default_arg);
      num_sources++;
    }
  //  cout<<"Num Sources = "<<num_sources<<endl;
  // Create the file, the tree and the branches...
  TTree* events;        
  TObjArray Forest(0);
  
  const char* name;
  
  for(i = 0; i < num_sources; i++)
    {      
      nume=0;
      fluence1=0.0;
      fluence2=0.0;
      fluence3=0.0;
      fluence4=0.0;
      fluence5=0.0;
  
      StatusCode sc =  m_fsvc->source(sources[i], m_flux);
      if( sc.isFailure()) 
	{
	  std::cout << "Could not find flux " << endl;
	  return sc;
	}
      cout<<" Source Name = "<<sources[i]<<endl;
      
      //name=sources[i].c_str();
      name=m_source_name;
      if (savef==true){
	events= new TTree(name,name);
	events->Branch("energy",&energy,"energy/D");
	events->Branch("time",&time,"time/D");
	events->Branch("Rate",&Rate,"Rate/D");
	events->Branch("cos_theta",&cos_theta,"cos_theta/D");
	events->Branch("phi",&phi,"phi/D");
	Forest.Add(events);
      }
      
      //sb pair<double,double> loc=m_fsvc->location();

      //      cout << loc.first << "   " << loc.second <<endl;
      time=1.0e-4;
      double t1;
      t1=time;
      while(time<=time_max && nume<=events_max)
	{
	  m_flux->generate();  
	  time=m_flux->time();
	  dir = m_flux->launchDir();
	  energy = m_flux->energy(); // kinetic energy in MeV
	  Area=m_flux->targetArea();
	  Rate= m_flux->rate();
	  dt=time-t1;
	  t1=time;
	  // Calculate the Fluences 
	  fluence1+=CalculateFluence(energy);
	  fluence2+=CalculateFluence(energy,0.05,0.3);
	  fluence3+=CalculateFluence(energy,2.5,5.0);
	  fluence4+=CalculateFluence(energy,5.0,10.0);
	  fluence5+=CalculateFluence(energy,10.0,1000.0);

	  cos_theta = dir.z();
	  phi = atan2(dir.y(),dir.x());
	  if(phi < 0) phi = 2*M_PI + phi;

	  phi=180*phi/M_PI; //degrees

	  if (savef==true) events->Fill();
	  if (nume%10==0){
	    cout<<
	      "-------- Event Number: "<<nume<<"\n"<<
	      " Time [s] = "<<time<<"\n"<<
	      " Rate [ph/(s)]= "<<Rate<<"\n"<<
	      // " Flux [ph/(m^2 s)]= "<<e->flux(time)<<"\n"<<
	      " 1/Rate [s]= "<<1/Rate<<"\n"<<
	      " Interval [s]= "<<dt<<"\n"<<
	      " Area [m^2]= "<<Area<<"\n"<<
	      // " --------------------------------\n"<<
	      " Energy of Photon Extracted [ MeV ]= "<<energy<<"\n"<<
	      " Direction: Cos(theta) = " << cos_theta <<", phi = "<<phi<<"\n"<<
	      endl;
	  }
	  nume++;
	}
      cout<<"Time final="<<time<<endl;
      cout<<"Number of events processed ="<<nume<<endl;
      if (savef==true) events->Print();
      cout<<"Fluence [erg/cm^2]="<<fluence1/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
      cout<<"Fluence (0.05 MeV - 0.3 MeV) [erg/cm^2]="<<fluence2/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
      cout<<"Fluence (2.5 - 5 MeV) [erg/cm^2]="<<fluence3/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
      cout<<"Fluence (5 MeV - 10 MeV)[erg/cm^2]="<<fluence4/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
      cout<<"Fluence (10 MeV - 1GeV)[erg/cm^2]="<<fluence5/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
      // if (savef==true) events->Scan("energy:time:Rate:cos_theta:phi");
    } // For all the sources...
  
  if (savef==true){
    std::string paramFile2 = "$(GRBROOT)/src/test/GRBdata.txt";
    facilities::Util::expandEnvVar(&paramFile2);
	std::ofstream f2(paramFile2.c_str(),ios::app);
    f2<<time<<endl;
    f2<<(Area*1.0e+4)<<endl;
    f2<<fluence1/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
    f2<<fluence2/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
    f2<<fluence3/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
    f2<<fluence4/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
    f2<<fluence5/(Area*1.0e+4)*(1.0/cst::erg2MeV)<<endl;
    f2.close();
    
    TFile f("Events.root","UPDATE");
    Forest.Write();
    f.Close();
  }
}

