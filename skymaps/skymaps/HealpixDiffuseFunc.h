/** @file HealpixDiffuseFunc.h
    @brief declare class HealpixDiffuseFunc

$Header$

*/
#ifndef skymaps_HealpixDiffuseFunc_h
#define skymaps_HealpixDiffuseFunc_h

#include "skymaps/SkySpectrum.h"
#include "skymaps/SkyImage.h"

#include "healpix/HealpixArray.h"
#include "tip/IFileSvc.h"

#include "astro/SkyFunction.h"
#include "astro/SkyDir.h"

#include <vector>
#include <cassert>

namespace skymaps { 

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/** @class HealpixDiffuseFunc
    @brief a SkyFunction that adapts a diffuse map. also includes extragal diffuse

*/

class HealpixDiffuseFunc : public skymaps::SkySpectrum {
public:

    /** @brief ctor that reads a Healpix SkyMap represention of the diffuse, with multple layers for
         eneries. 
         @param diffuse_healpix_file Name of file. It must have an extension ENERGIES with the corresponding energy valuse
         @param energy[1000] initial energy for the SkyFunction 
         @param interpolate[true] interpolate the input map

    */
    enum unitType {COUNTS,DIFFCOUNTS,DENSITY,DIFFDENSITY,FLUX};
    
    HealpixDiffuseFunc(const std::string& diffuse_healpix_file, unitType u=COUNTS, double exposure=1., double energy=1000., bool interpolate=true);
 
    virtual ~HealpixDiffuseFunc();

    double isotropicFlux(double energy) const; ///< access to an isotropic flux component

    ///@brief interpolate table 
    ///@param e energy in MeV
    virtual double value (const astro::SkyDir& dir, double e) const;

    ///@brief integral for the energy limits, in the given direction
    virtual double integral(const astro::SkyDir& dir, double a, double b) const;

    virtual std::string name() const {return m_name;};


    //-------------------------------------------------------
    /** @brief set vector of values for set of energy bins
        @param dir  direction 
        @param energies vector of the bin edges.
        @return result vector of the values
    */
    
    std::vector<double> integral(const astro::SkyDir& dir, const std::vector<double>&energies) const;

    /// @return number of layers
    size_t layers()const { return m_energies.size();}
    
#ifndef SWIG    

    class FitsIO {
       public:
          FitsIO::FitsIO(const std::string & filename);
          FitsIO::~FitsIO();
	  
	  healpix::HealpixArray<std::vector<double> >& skymap(){ return *m_skymap;};
	  std::vector<double>& energies(){ return m_energies; };
       
       private:
          void read(const std::string & filename);
	  	  
          tip::IFileSvc& fileSvc; 
          healpix::HealpixArray<std::vector<double> > * m_skymap;
	  std::vector<double> m_energies;
    };
    
#endif
private:

    std::string m_name;
    FitsIO m_fitio;
    healpix::HealpixArray<std::vector<double> >& m_skymap; ///< skymap
    std::vector<double>& m_energies; ///< list of energies
    unitType m_unit;
    double m_exposure;
    
    size_t layer(double e)const;

    double m_emin, m_emax;
    double m_solidAngle;
};
} // namespace skymaps
#endif

