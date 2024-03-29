/**
 * @file gtexphpsun.cxx
 * @brief Application for creating binned exposure maps for moving sources
 * @author G. Johannesson
 *
 * $Header$
 */

#include <cmath>
#include <cstdlib>
#include <cstring>

#include <memory>
#include <stdexcept>

#include "st_stream/StreamFormatter.h"

#include "st_app/AppParGroup.h"
#include "st_app/StApp.h"
#include "st_app/StAppFactory.h"

#include "tip/IFileSvc.h"
#include "tip/Image.h"
#include "tip/Header.h"

#include "dataSubselector/Gti.h"

#include "Likelihood/AppHelpers.h"
#include "SolarSystemTools/HealpixExposureSun.h"
#include "SolarSystemTools/Observation.h"

using namespace SolarSystemTools;

class ExpHpSun : public st_app::StApp {
public:
   ExpHpSun();
   virtual ~ExpHpSun() throw() {
      try {
         delete m_helper;
      } catch (std::exception &eObj) {
         std::cerr << eObj.what() << std::endl;
      } catch (...) {
      }
   }
   virtual void run();
   virtual void banner() const;
private:
	 Likelihood::AppHelpers * m_helper;
   st_app::AppParGroup & m_pars;
   double m_srRadius;
   void promptForParameters();
   void set_phi_status();
   void generateEnergies(std::vector<double> & energies) const;
   void copyGtis() const;
   void copyHeaderKeywords() const;
   void copyDssKeywords(tip::Header & header) const;
   static std::string s_cvs_id;
};

st_app::StAppFactory<ExpHpSun> myAppFactory("gtexphpsun");

std::string ExpHpSun::s_cvs_id("$Name$");

ExpHpSun::ExpHpSun() : st_app::StApp(), m_helper(0), 
                     m_pars(st_app::StApp::getParGroup("gtexphpsun")) {
   setVersion(s_cvs_id);
}

void ExpHpSun::banner() const {
   int verbosity = m_pars["chatter"];
   if (verbosity > 2) {
      st_app::StApp::banner();
   }
}

void ExpHpSun::run() {
   promptForParameters();

   std::string ltcube_file = m_pars["infile"];

   bool useEbounds(true);
   std::string bincalc = m_pars["bincalc"];
   if (bincalc == "CENTER") {
      useEbounds = false;
   }

   m_helper = new Likelihood::AppHelpers(&m_pars, "none");
   set_phi_status();
   m_helper->checkOutputFile();
   ExposureCubeSun ltcube; 
	 SolarSystemTools::Observation observation(m_helper->observation(), &ltcube);
	 ltcube.setEfficiencyFactor(observation.respFuncs().efficiencyFactor());
   ltcube.readExposureCubeSun(ltcube_file);

// Create map for user-defined geometry.
   std::vector<double> energies;
   generateEnergies(energies);
   if (!useEbounds) {
      for (size_t k(0); k < energies.size() - 1; k++) {
         energies[k] = std::sqrt(energies[k]*energies[k+1]);
      }
      energies.pop_back();
   }
   HealpixExposureSun bexpmap(energies, observation, &m_pars);
   bexpmap.writeOutput(m_pars["outfile"]);
   copyGtis();
}

void ExpHpSun::generateEnergies(std::vector<double> & energies) const {
   energies.clear();
   std::string ebinalg = m_pars["ebinalg"];
   if (ebinalg == "FILE") {
      std::string ebinfile = m_pars["ebinfile"];
      const tip::Table * energybins = 
         tip::IFileSvc::instance().readTable(ebinfile, "ENERGYBINS");
      tip::Table::ConstIterator it = energybins->begin();
      tip::ConstTableRecord & row = *it;
      double energy;
      double emax;
      for ( ; it != energybins->end(); ++it) {
         row["E_MIN"].get(energy);
         // Note that energies in gtbindef output are in units of keV.
         energies.push_back(energy/1e3);
         row["E_MAX"].get(emax);
      }
      energies.push_back(emax/1e3);
      delete energybins;
   } else {
      double emin = m_pars["emin"];
      double emax = m_pars["emax"];
      int enumbins = m_pars["enumbins"];
      double estep = std::log(emax/emin)/enumbins;
      for (size_t k(0); k < enumbins + 1; k++) {
         energies.push_back(emin*std::exp(estep*k));
      }
   }
}

void ExpHpSun::promptForParameters() {
   m_pars.Prompt("infile");
   m_pars.Prompt("outfile");
   m_pars.Prompt("irfs");
   m_pars.Prompt("evtype");
   m_pars.Prompt("binsz");
   std::string ebinalg = m_pars["ebinalg"];
   if (ebinalg == "FILE") {
      m_pars.Prompt("ebinfile");
   } else {
      m_pars.Prompt("emin");
      m_pars.Prompt("emax");
      m_pars.Prompt("enumbins");
   }
   m_pars.Save();
}

void ExpHpSun::set_phi_status() {
   // If indicated, turn off phi-dependence for all IRFs.
   bool ignorephi = m_pars["ignorephi"];
   if (ignorephi) {
      const Likelihood::Observation & observation(m_helper->observation());
      std::map<unsigned int, irfInterface::Irfs *>::const_iterator respIt 
         = observation.respFuncs().begin();
      for ( ; respIt != observation.respFuncs().end(); ++respIt) {
         respIt->second->aeff()->setPhiDependence(false);
      }
   }
}

void ExpHpSun::copyGtis() const {
   std::string infile = m_pars["infile"];
   dataSubselector::Gti gti(infile);
   std::string outfile = m_pars["outfile"];
   gti.writeExtension(outfile);
}

void ExpHpSun::copyHeaderKeywords() const {
   std::string infile = m_pars["infile"];
   std::string inext("EXPOSURE");
   const tip::Table * intab = 
     tip::IFileSvc::instance().readTable(infile, inext);
   const tip::Header & inheader(intab->getHeader());
   
   std::string outfile = m_pars["outfile"];
   std::string outext("PRIMARY");
   tip::Image * outimg = tip::IFileSvc::instance().editImage(outfile, outext);
   tip::Header & outheader(outimg->getHeader());

   // Unfortunately TIP does not provide access to header comments, so
   // we cannot copy them using it. Could use cfitsio directly but
   // prefer TIP as it is standard here.

#define COPYKEYWORD(type, name)			\
   try {					\
     type x;					\
     inheader[name].get(x);			\
     outheader[name].set(x);			\
   } catch(...) {				\
   }
   
   COPYKEYWORD(std::string, "DATE-OBS");
   COPYKEYWORD(std::string, "DATE-END");
   COPYKEYWORD(double,      "TSTART");
   COPYKEYWORD(double,      "TSTOP");
   COPYKEYWORD(double,      "MJDREFI");
   COPYKEYWORD(double,      "MJDREFF");
   COPYKEYWORD(std::string, "TIMEUNIT");
   COPYKEYWORD(double,      "TIMEZERO");
   COPYKEYWORD(std::string, "TIMESYS");
   COPYKEYWORD(std::string, "TIMEREF");
   COPYKEYWORD(bool,        "CLOCKAPP");
   COPYKEYWORD(bool,        "GPS_OUT");

#undef COPYKEYWORD

   copyDssKeywords(outheader);

   delete outimg;
   delete intab;
}

void ExpHpSun::copyDssKeywords(tip::Header & header) const {
   std::string cmap_file = m_pars["cmap"];
   dataSubselector::Cuts * irfs_cuts(0);
   if (cmap_file == "none") {
      // No DSS keywords to copy from input files, so just write
      // selected irfs.
      irfs_cuts = new dataSubselector::Cuts();
   } else {
      // Copy DSS keywords from input cmap file, ensuring that the
      // irfs version is set.
      irfs_cuts = new dataSubselector::Cuts(cmap_file, "PRIMARY", false,
                                            false, false);
   }
   irfs_cuts->addVersionCut("IRF_VERSION", m_helper->irfsName());
   irfs_cuts->writeDssKeywords(header);
   delete irfs_cuts;
}
