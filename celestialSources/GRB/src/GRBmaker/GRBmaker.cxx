// FILE: GRBmaker.cxx

// This class is instantiated in two ways:
// -  Input: Filename
//		 In this mode, it will read the photon list (time,energy) generated by the first option if filename is not empty,
//			Otherwise, it creates "n" bursts
// -  Input: duration, flux, fraction, power law index, npulse, flag
//		 In this mode, it creates a photon list for the burst specified by the input parameters and if the flag is set,
//			records it in a file
//

#include "GRBmaker.h"
#include "GRB.h"
#include "LatGrb.h"
#include "GbmGrb.h"
#include "CLHEP/Random/RandFlat.h"

using namespace grbobstypes;




// create(const std::vector<std::string> &paramVector)
// Creates LAT and GBM GRBs
//
// Input:
//		paramVector					:	directory and filename for GRB data
//      grbcst::seed                :   constant
//
// Output:
//      LAT and GBM Objects
//
// Calls:
//      HepRandom::getTheEngine 
//      HepRandom::setTheSeed
//      createGRB 
//      setSpecnorm 
//
// Caller:
//		interface to the simulation

GRB *GRBmaker::create(const std::vector<std::string> &paramVector)
{
    if (paramVector.size() == 2)
        return new GRB(paramVector);
    
    else if (paramVector.size() <= 1)
    {
        // Get an engine and set its seed
        HepRandomEngine *engine = HepRandom::getTheEngine();
        HepRandom::setTheSeed(grbcst::seed);
        
        LatGrb *latGrb = new LatGrb(engine, "LAT", paramVector[0]);
        //GbmGrb *gbmGrb = new GbmGrb(engine, "GBM", latGrb->specnorm(), paramVector[0]);
        
        //delete gbmGrb;
        return latGrb;
    }
    
    else
    {
        std::cout << "invalid number of parameters" << std::endl;
        return 0;
    }
}



// create(const double duration, const int npuls, const double flux, const double fraction, 
//		  const double alpha, const double beta, const double epeak, const double specnorm, const bool flag)
//
// Creates LAT and GBM GRBs
//
// Creates the photon list (time,energy) for the burst specified by the input parameters 
//		and records it in a file if the flag is set.
//
// Input:
//		engine						:	pointer to a HepRandomEngine object
//      grbcst::seed                :   constant
//		duration					:	burst duration 
//      npuls                       :   number of pulses in current burst
//		flux						:	peak flux
//      fraction                    :   fraction
//		alpha						:   broken power law index
//		beta						:	broken power law index
//      epeak                       :   
//		specnorm					:	spectral normalization 
//      flag                        :   true : write GRB data to a file
//		grbcst::nbsim				:	long
//
// Output:
//		LAT and GBM objects
//
// Calls:
//      HepRandom::getTheEngine 
//      HepRandom::setTheSeed 
//      createGRB 
//
// Caller:
//		interface to the simulation

GRB *GRBmaker::create(const double duration, const int npuls, const double flux, const double fraction, 
                      const double alpha, const double beta, const double epeak, const double specnorm, const bool flag)
{
    // Get an engine and set its seed
    HepRandomEngine *engine = HepRandom::getTheEngine();
    HepRandom::setTheSeed(grbcst::seed);
    
    LatGrb *latGrb = new LatGrb(engine, duration, npuls, flux, fraction, alpha, beta, epeak, specnorm, flag);
    GbmGrb *gbmGrb = new GbmGrb(engine, duration, npuls, flux, fraction, alpha, beta, epeak, specnorm, flag);
    
    delete gbmGrb;
    return latGrb;
}



// clone()
// Makes a copy of itself and returns it to the caller.
//
// Input:
//		this						:	pointer to the GRBmaker object to be duplicated
//
// Output:
//		GRBmaker object				:	pointer to the newly created copy of the object pointed to by the "this" pointer
//
// Calls:
//		GRBmaker(const GRBmaker &)
//
// Caller:
//     interface to the simulation

GRBmaker *GRBmaker::clone() const
{
    return new GRBmaker(*this);
}



