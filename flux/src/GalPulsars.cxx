/** 
* @file GalPulsars.cxx
* @brief definition of GalPulsars
*
*/

#include "flux/Spectrum.h"
#include "flux/SpectrumFactory.h"
#include "flux/EventSource.h"
#include "astro/EarthOrbit.h"
//#include "astro/jplephem.h"
#include "CLHEP/Random/RandFlat.h"
#include "facilities/Util.h"
#include <string>
#include <utility>
#include <algorithm>
#include <vector>
#include <fstream>

// Used only for the testing function "writeCorrections"
#include "astro/SolarSystem.h"

class GalPulsars : public Spectrum
{
public:

   GalPulsars(const std::string& params);

   std::pair<double,double> dir(double energy);
   float operator()(float xi) const;

   double interval(double time);
   double energy(double time);

   virtual std::string title() const{return "GalPulsars";}
   virtual const char * particleName() const {return "gamma";}
   inline  const char * nameOf() const {return "GalPulsars";}

private:
   
   /// Writes out time, JD, Barycenter Location, TDB-TT, Shapiro Delay, and Geometric Delay
   void writeCorrections(void);

   void updateIntervals(double current_time, double time_decrement);
   double period(double jd, int pulsarIndex) const;
   double power_law( double r, double e1, double e2, double gamma) const;
   void initLightCurve(void);

   std::vector< std::vector<double> > m_lc; // Light Curves
   std::vector< std::string > m_name;  // Name of source
   std::vector<double> m_spectralIndex;  // Spectral Index of power law
   std::vector<double> m_highCutoff; // High energy cutoff in GeV
   std::vector<double> m_lowCutoff; // Low energy cutoff in GeV
   std::vector<double> m_flux;  // Flux in particles/cm^2/s
   std::vector<double> m_freq_dot; // Rate of change in frequency at reference time
   std::vector<double> m_freq; // Frequency at reference time
   std::vector<double> m_lat; // Galactic B coordinate
   std::vector<double> m_lon; // Galactic L coordinate
   std::vector<double> m_t0;  // Reference time for phase zero given as JD
   std::vector<bool> m_binary; // Flag true if pulsar is in a binary system

   std::vector<double> m_interval;
   int m_changed;
};

static SpectrumFactory<GalPulsars> factory;
const ISpectrumFactory& GalPulsarsFactory = factory;

GalPulsars::GalPulsars(const std::string& paramString)
{
   std::vector<std::string> params;
   facilities::Util::stringTokenize(paramString, ", ", params);

   facilities::Util::expandEnvVar(&params[0]);
   std::ifstream input_file(params[0].c_str(), std::ios::in);

   if(!input_file.is_open())
   {
      std::cerr << "Error:  Unable to read input file" << std::endl;
      return;
   }

   // Skip first line containing header information
   char buffer[1024];
   input_file.getline(buffer,1024);

   while(!input_file.eof())
   {
      // Check to see if the first character is valid for a name
      input_file.getline(buffer,1024,'\t');
      if(!isalnum(buffer[0]))
         break;

      m_name.push_back(buffer);

      input_file.getline(buffer,1024,'\t'); 
      m_lat.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t'); 
      m_lon.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t'); 
      m_freq.push_back(1./std::atof(buffer));

      input_file.getline(buffer,1024,'\t'); 
      m_freq_dot.push_back(-std::atof(buffer)*m_freq.back()*m_freq.back());

      input_file.getline(buffer,1024,'\t');
      m_flux.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t');
      m_lowCutoff.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t');
      m_highCutoff.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t');
      m_spectralIndex.push_back(std::atof(buffer));

      input_file.getline(buffer,1024,'\t');
      m_t0.push_back(2400000.5+std::atof(buffer));

      input_file.getline(buffer,1024,'\t');
      if(buffer[0] == 'Y' || buffer[0] == 'y')
         m_binary.push_back(true);
      else
         m_binary.push_back(false);

      input_file.getline(buffer,1024,'\t');
      int numbins = std::atoi(buffer);

      std::vector<double> temp_lc;
      for(int i = 0; i < numbins - 1; i++)
      {
         input_file.getline(buffer,1024,'\t');
         temp_lc.push_back(std::atof(buffer));
      }
      input_file.getline(buffer,1024,'\n'); 
      temp_lc.push_back(std::atof(buffer));

      m_lc.push_back(temp_lc);
      temp_lc.clear();
   }
   input_file.close();

   m_changed = -1;
   m_interval.resize(m_flux.size());

   initLightCurve();

   // Test function
   writeCorrections();
}


double GalPulsars::interval(double current_time) 
{
   // Initialize the intervals for all the pulsars if this is being called for the first time
   if(m_changed == -1)
      updateIntervals(current_time,0.);

   // Find the index of the shortest interval
   m_changed = 0;
   for(unsigned int i = 1; i < m_interval.size(); i++)
   {
      if(m_interval[i] < m_interval[m_changed]) 
         m_changed = i;
   }

   // Store the shortest interval before calling the update
   double shortestinterval = m_interval[m_changed];
   
   // Update the intervals
   updateIntervals(current_time, shortestinterval);

   return shortestinterval;
}

void GalPulsars::updateIntervals(double current_time, double time_decrement)
{
   // Loop over all sources
   for(unsigned int i = 0; i < m_interval.size(); i++)
   {
      // Update all sources that need a new interval
      if(m_changed == i || m_changed == -1)
      {
         astro::EarthOrbit orbit;
         astro::JulianDate tt(orbit.dateFromSeconds(current_time));

         // Convert times to tdb since pulsar times are given in tdb time system
         double tdb = tt + orbit.tdb_minus_tt(tt)/86400.;
         double dt = (tdb - m_t0[i])*86400;

         // Calculate a dimensionless target number based on the Poisson distribution
         double target = -std::log(1.-RandFlat::shoot(1.));

         double area = 1.0e4 * EventSource::totalArea();
         double current_period = period(tdb,i);

         double num_per_cycle = m_flux[i]*area*current_period;
         double num_cycles = floor(target/num_per_cycle);

         m_interval[i] = current_period * num_cycles;

         // Get source direction for Shapiro delay and geometric delay calculations
         std::pair<double,double> lb;
         lb.first = m_lon[i];
         lb.second = m_lat[i];
         astro::SkyDir s_dir(lb.first,lb.second,astro::SkyDir::GALACTIC);

         double traveltime = orbit.calcTravelTime(tdb,s_dir);

         double cycle_fraction = fmod(m_freq[i]*dt + 0.5 * m_freq_dot[i]*dt*dt
            + (orbit.calcShapiroDelay(tdb,s_dir) + orbit.calcTravelTime(tdb,s_dir))/current_period, 1.);

         // Determine phase of the pulsar for the current time
         int phase_index = (int) floor(cycle_fraction * m_lc[i].size());
         if(phase_index == m_lc[i].size()) 
            phase_index = 0;

         double current = num_per_cycle * num_cycles;

         // Start sum by subtracting off part of bin that isn't used
         double phase_sum = - m_lc[i][phase_index] * (cycle_fraction * m_lc[i].size() - 1.0 * phase_index) 
                            * area * (current_period / m_lc[i].size());

         // Find out which bin corresponds to the target
         for(unsigned int j = 0; j < 2 * m_lc[i].size() + 1; j++)
         {
            // For each bin add rate * bin-time 
            phase_sum += m_lc[i][phase_index] * area * (current_period / m_lc[i].size());

            if(current + phase_sum > target)
            {
               m_interval[i] += (j+1.)*current_period / m_lc[i].size();
               m_interval[i] -= current_period / m_lc[i].size() * (current + phase_sum - target) / (m_lc[i][phase_index] * area * (current_period / m_lc[i].size()));
              
               break;
            }
            else
            {
               phase_index++; 
               if(phase_index == m_lc[i].size()) phase_index = 0;
            }
         }

      }
      else
         m_interval[i] -= time_decrement;
   }
} 

double GalPulsars::period(double jd, int pulsarIndex) const {
   return 1./m_freq[pulsarIndex] + (-m_freq_dot[pulsarIndex]/(m_freq[pulsarIndex]*m_freq[pulsarIndex]))*(jd - m_t0[pulsarIndex])*86400;
}

std::pair<double,double> GalPulsars::dir(double energy)
{
   if(m_changed == -1)
   {
      std::cout << "Warning:  interval should be called before dir when using GalPulsars class." << std::endl;
   }

   // return direction in galactic coordinates
   return std::make_pair<double,double>(m_lon[m_changed],m_lat[m_changed]);
}

float GalPulsars::operator()(float xi) const {

   if(m_changed == -1)
   {
      std::cout << "Warning:  interval should be called before () when using GalPulsars class." << std::endl;
   }

    // single power law, or first segment
    return static_cast<float>(power_law(xi, m_lowCutoff[m_changed], m_highCutoff[m_changed], 1. + m_spectralIndex[m_changed]));
}

double GalPulsars::energy(double time) {
   return (*this)(RandFlat::shoot());
}


// differential rate: return energy distrbuted as e**-gamma between e1 and e2, if r is uniform from 0 to 1
double GalPulsars::power_law( double r, double e1, double e2, double gamma) const
{
   return gamma==1
           ?  e1*exp(r*log(e2/e1))
           :  e1*exp(log(1.0 - r*(1.-pow(e2/e1,1-gamma)))/(1-gamma));
}

// verify that light curve agrees with flux for each source
void GalPulsars::initLightCurve(void)
{
   for(unsigned int i = 0; i < m_lc.size(); i++)
   {
      double rate = 0;
      for(unsigned int j = 0; j < m_lc[i].size(); j++)
         rate += m_lc[i][j] / m_lc[i].size();

      double scaling_factor = m_flux[i] / rate;

      for(unsigned int k = 0; k < m_lc[i].size(); k++)
         m_lc[i][k] *= scaling_factor;
   }
}


/// Writes out time, JD, Barycenter Location, TDB-TT, Shapiro Delay, and Geometric Delay
void GalPulsars::writeCorrections(void)
{
   /**** Commented out until changes in astro are finished

   std::ofstream cFile;
   cFile.open("timings.txt",std::ios::out);

   // Start at mission start and write out corrections once per day for 1 year with a test source
   // located at galactic center.
   astro::EarthOrbit orbit;
   astro::jplephem ephemeris;
   Hep3Vector barycenter;
   double tdb_minus_tt;
   double shapiroDelay;
   double geometricDelay;

   astro::SkyDir galCenter(0.0,0.0,astro::SkyDir::GALACTIC);

   std::cout << "Galactic Center RA/DEC: " << galCenter.ra() << "\t" << galCenter.dec() << std::endl;

   cFile << "Time TT BaryRA   BaryDec  TDB-TT   Shapiro  Geometric" << std::endl;

   for(double time = 0; time < 86400 * 365; time += 86400)
   {
      astro::JulianDate tt(orbit.dateFromSeconds(time));
      barycenter = ephemeris.getBarycenter(tt);
      tdb_minus_tt = orbit.tdb_minus_tt(tt);
      shapiroDelay = orbit.calcShapiroDelay(tt,galCenter);
      geometricDelay = orbit.calcTravelTime(tt,galCenter);
      double ra = atan2(barycenter.y(),barycenter.x()) * 180. / M_PI;
      double dec = atan2(barycenter.z(), sqrt(barycenter.x()*barycenter.x()
                         + barycenter.y()*barycenter.y())) * 180. / M_PI;

      cFile.precision(14);
      cFile.setf(std::ios::scientific);
      cFile << time << "\t" << tt << "\t" << ra << "\t" << dec << "\t" << tdb_minus_tt << "\t" 
         << shapiroDelay << "\t"  << geometricDelay << std::endl;
   }
   
   cFile.close();
*/
}

