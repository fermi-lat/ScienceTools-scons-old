/** \file GrbResponse.h
    \brief Interface for Grb-specific response calculations.
    \author James Peachey, HEASARC
*/
#ifndef rspgen_GrbResponse_h
#define rspgen_GrbResponse_h
#include <string>

#include "evtbin/Binner.h"

#include "latResponse/Irfs.h"

#include "rspgen/IWindow.h"

#include "tip/Header.h"

namespace rspgen {

  /** \class GrbResponse
      \brief Interface for Grb-specific response calculations.
  */
 
  class GrbResponse {
    public:
      /** \brief Create GrbResponse object for a given burst and spacecraft coordinates
          \param theta The inclination angle of the spacecraft wrt the GRB direction.
          \param true_en_binner Binner object which is cloned and used for true energy binning.
          \param app_en_binner Binner object which is cloned and used for apparent energy binning.
          \param irfs The IRFs object, used to get the response functions from caldb.
          \param window The window object, used to define integration regions.
      */
      GrbResponse(double theta, const evtbin::Binner * true_en_binner, const evtbin::Binner * app_en_binner,
        latResponse::Irfs * irfs, const IWindow * window);

      /** \brief Create GrbResponse object for a given burst and spacecraft coordinates
          \param grb_ra The ra of the burst.
          \param grb_dec The dec of the burst.
          \param grb_time The time of the burst.
          \param psf_radius The radius of the psf integration, in degrees.
          \param resp_type Identifies response function type.
          \param spec_file The name of the spectrum file.
          \param sc_file The name of the file containing spacecraft data.
          \param true_en_binner Binner object used for true energy bin definitions.
      */
      GrbResponse(double grb_ra, double grb_dec, double grb_time, double psf_radius, const std::string resp_type,
        const std::string & spec_file, const std::string & sc_file, const evtbin::Binner * true_en_binner);

      virtual ~GrbResponse() throw();

      /** \brief Compute responses and write them to eh output file.
          \param creator String to write for the CREATOR keyword.
          \param file_name Name of the output file.
      */
      virtual void writeOutput(const std::string & creator, const std::string & file_name, const std::string & fits_template);

      /** \brief Compute the response for the given value of true energy.
          \param true_energy The energy for which to compute response.
          \param response The response (vector of apparent energy bins).
      */
      virtual void compute(double true_energy, std::vector<double> & response);

    private:
      static const double s_keV_per_MeV = 1000.;

      tip::Header::KeyValCont_t m_kwds;
      double m_theta;
      evtbin::Binner * m_true_en_binner;
      evtbin::Binner * m_app_en_binner;
      latResponse::Irfs * m_irfs;
      IWindow * m_window;
  };

}

#endif
