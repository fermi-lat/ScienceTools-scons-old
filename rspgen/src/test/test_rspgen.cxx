/** \file test_rspgen.cxx
    \brief Test application for response generator code.
    \author Yasushi Ikebe, James Peachey
*/
// C++ standard inclusions.
#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <typeinfo>
#include <vector>

// Main appliation class RspGenApp.
#include "RspGenApp.h"

// Sky directions use astro::SkyDir.
#include "astro/SkyDir.h"

// From evtbin, generic histograms and associated binners are used.
#include "evtbin/Hist1D.h"
#include "evtbin/Binner.h"
#include "evtbin/LinearBinner.h"
#include "evtbin/OrderedBinner.h"

// From latResponse, use instrument response function abstractions.
#include "latResponse/Irfs.h"
#include "latResponse/IrfsFactory.h"

// Tests include circular region (window) abstractions.
#include "rspgen/CircularWindow.h"

// Response abstraction for burst case.
#include "rspgen/GrbResponse.h"

// Response abstraction for burst case.
#include "rspgen/PointResponse.h"

// Standard application-related code.
#include "st_app/StApp.h"
#include "st_app/StAppFactory.h"

// Table access through tip.
#include "tip/IFileSvc.h"
#include "tip/LinearInterp.h"
#include "tip/Table.h"

// Obvious unit conversion.
static double s_keV_per_MeV = 1000.;

/** \class RspGenTestApp
    \brief The main test application itself.
*/
class RspGenTestApp : public st_app::StApp {
  public:
    /// \brief Construct a test application.
    RspGenTestApp();

    virtual ~RspGenTestApp() throw() {}

    /// \brief Run all tests, reporting failures.
    void run();

    /** \brief Simple test in which apparent energy bins are read from ebounds, but true energy bins are completely
        fabricated. Also a single random direction is chosen for sc pointing exactly coincident with the photon direction.
        This amounts to the case of a GRB. The psf is integrated over a circular region with an arbitrary radius.
        This test produces test_response1.rsp.
    */
    void test1();

    /** \brief Simple test much like test 1, except the true energy bins are read from a bin file.
        This test produces test_response2.rsp.
        \param ps_ra The true photon RA in degrees
        \param ps_dec The true photon DEC in degrees
        \param radius The radius of psf integration in degrees.
        \param file_name The name of the output response file.
    */
    void test2(double ps_ra, double ps_dec, double radius, const std::string & file_name);

    /** \brief Like test2, but consistent with a steady point source observed over a period of time. Thus the
        sc data file is read, and sc positions are binned on theta wrt point source direction.
        This test produces test_response3.rsp.
    */
    void test3();

    /** \brief Test utilizing GrbResponse class to compute response for a fictitious grb. The sc data are
        interpolated for the time of the burst to give a sc pointing. The burst was assumed to be close to this
        value so that the angle theta will be non-0 but small.
        This test produces test_response4.rsp.
    */
    void test4();

    /** \brief Repeat test 2, using photon direction identical to that in test 4. Apart from keywords, the spectrum
        in this test should be the same as that written by test 4.
        This test produces test_response5.rsp.
    */
    void test5();

    /** \brief Test RspGenApp class for GrbResponse.
    */
    void test6();

    /** \brief Test utilizing PointResponse class to compute response for a given point source direction. The sc data are
        binned to give a differential exposure. This is then integrated to produce the total response in the sc file.
        This test produces test_response7.rsp.
    */
    void test7();

    /** \brief Test RspGenApp class for PointResponse.
    */
    void test8();

  private:
    /** \brief Return a standard energy binner used throughout the tests.
    */
    evtbin::Binner * createStdBinner();

    std::string m_data_dir;
    bool m_failed;
};

RspGenTestApp::RspGenTestApp(): m_data_dir(), m_failed(false) {
  // Get the root directory from which to find the input data files.
  const char * data_dir = getenv("RSPGENROOT");
  if (0 != data_dir) m_data_dir = data_dir;
  m_data_dir += "/data/";
}

void RspGenTestApp::run() {
  // Run all tests in order.
  test1();
  // Arbitrary sky direction (120., 30.). Arbitrary radius of psf integration == .1
  test2(120., 30., .1, "test_response2.rsp");
  test3();
  test4();
  test5();
  test6();
  test7();
  test8();
  if (m_failed) throw std::runtime_error("test_rspgen failed");
}

// Test just getting values from latResponse for an arbitrary simple case.
void RspGenTestApp::test1() {
  double ra_ps = 120.; // RA of point source
  double dec_ps = 30.; // DEC of point source
  double ra_scz = 120.; // RA of spacecraft Z axis
  double dec_scz = 30.; // DEC of spacecraft Z axis

  // Open input pha file.
  std::auto_ptr<const tip::Table> ebounds_ext(tip::IFileSvc::instance().readTable(m_data_dir + "PHA1.pha", "EBOUNDS"));

  // Read the detchans keyword. This determines the number of channels used for apparent energy.
  int detchans = 0;
  ebounds_ext->getHeader()["DETCHANS"].get(detchans);

  // Make sure there are at least detchans channels in the input ebounds. This is just a basic sanity check.
  tip::Index_t num_rec = ebounds_ext->getNumRecords();
  if (num_rec < detchans) throw std::runtime_error("test1: Channel number mismatch");
  std::vector<double> min_app_en(detchans);
  std::vector<double> max_app_en(detchans);

  tip::Index_t index = 0;
  for (tip::Table::ConstIterator ebounds_itor = ebounds_ext->begin(); ebounds_itor != ebounds_ext->end(); ++ebounds_itor) {
    (*ebounds_itor)["CHANNEL"].get(index);
    if (index > detchans) continue; // Skip any rows with channel numbers > the number of channels.
    // Warning: This assumes first channel is 1, but that is not necessarily true. Check TLMIN/TLMAX keywords
    --index; // Arrays start with 0, channels with 1.
    (*ebounds_itor)["E_MIN"].get(min_app_en[index]);
    (*ebounds_itor)["E_MAX"].get(max_app_en[index]);
    min_app_en[index] /= s_keV_per_MeV;
    max_app_en[index] /= s_keV_per_MeV;
  }
  // Add a check here to make sure all the channels were set. We can't compute response if any are missing.
  
  // Make a couple directions.
  astro::SkyDir ps_dir(ra_ps, dec_ps);
  astro::SkyDir scz_dir(ra_scz, dec_scz);

  // Arbitrarily choose a response.
  latResponse::Irfs * irfs = latResponse::irfsFactory().create("DC1::Front");
  // First get psf.
  latResponse::IPsf * psf = irfs->psf();

  // Compute angle, which should be 0.
  double theta = ps_dir.difference(scz_dir) * 180. / M_PI;

  double phi = 0.;
  double radius = 0.1;

  // Create output response file from template:
  tip::IFileSvc::instance().createFile("test_response1.rsp", m_data_dir + "LatResponseTemplate");

  // Open the response file:
  tip::Table * resp_table = tip::IFileSvc::instance().editTable("test_response1.rsp", "MATRIX");

  resp_table->getHeader()["DETCHANS"].set(detchans);

  // Next get aeff.
  latResponse::IAeff * aeff = irfs->aeff();

  // And redistribution.
  latResponse::IEdisp * edisp = irfs->edisp();

  tip::Table::Iterator out_itor = resp_table->begin();

  // Arbitrarily set the number of channels used for "true" energy dimension.
  int num_true_chan = 1000;

  // Arrays used to write f_chan and n_chan columns, respectively.
  std::vector<int> f_chan(1, 1);
  std::vector<int> n_chan(1, detchans);

  // Create fake true energy bins, logarithmically spanning the GLAST spectrum.
  double offset = 2.;
  double factor = (6. - offset)/num_true_chan;
  for (long true_en_idx = 0; true_en_idx < num_true_chan; ++true_en_idx, ++out_itor) {
    double true_en = pow(10., (true_en_idx + .5) * factor + offset);
    double aeff_val = aeff->value(true_en, theta, phi);
    double int_psf_val = psf->angularIntegral(true_en, theta, phi, radius);

    // Populate response vector for each true energy value.
    std::vector<double> response;
    for (index = 0; index < detchans; ++index) {
      response.push_back(aeff_val * edisp->integral(min_app_en[index], max_app_en[index], true_en, theta, phi) * int_psf_val);
    }

    // Write response to file, converting to keV on the fly.
    (*out_itor)["ENERG_LO"].set(s_keV_per_MeV * pow(10., true_en_idx * factor + offset));
    (*out_itor)["ENERG_HI"].set(s_keV_per_MeV * pow(10., (true_en_idx + 1) * factor + offset));
    (*out_itor)["N_GRP"].set(1);
    (*out_itor)["F_CHAN"].set(f_chan);
    (*out_itor)["N_CHAN"].set(n_chan);
    (*out_itor)["MATRIX"].set(response);
  }
  
  // Write the ebounds extension.
  tip::Table * out_ebounds = tip::IFileSvc::instance().editTable("test_response1.rsp", "EBOUNDS");

  // Set detchans explicitly.
  out_ebounds->getHeader()["DETCHANS"].set(detchans);

  out_ebounds->setNumRecords(num_rec);

  // Just copy the input ebounds extension.
  tip::Table::ConstIterator in_itor = ebounds_ext->begin();
  for (out_itor = out_ebounds->begin(); out_itor != out_ebounds->end(); ++in_itor, ++out_itor) {
    *out_itor = *in_itor;
  }

  delete out_ebounds;
  delete resp_table;
  delete irfs;
}

// In this example. "true" energy comes from bin definition file.
void RspGenTestApp::test2(double ra_ps, double dec_ps, double radius, const std::string & file_name) {
  using namespace evtbin;

  // Make sure output will reveal small differences.
  std::cout.precision(24);

  // Create interval container for user defined bin intervals.
  OrderedBinner::IntervalCont_t intervals;

  // Open the file for true energy bin definition.
  std::auto_ptr<const tip::Table> table(tip::IFileSvc::instance().readTable(m_data_dir + "StdEnergyBin.fits", "ENERGYBINS"));

  // Iterate over the file, saving the relevant values into the interval array.
  for (tip::Table::ConstIterator itor = table->begin(); itor != table->end(); ++itor) {
    intervals.push_back(Binner::Interval((*itor)["START_BIN"].get(), (*itor)["STOP_BIN"].get()));
  }

  // Create binner from these intervals.
  OrderedBinner binner(intervals);
 
  long num_bins = binner.getNumBins();

  double ra_scz = ra_ps; // RA of spacecraft Z axis
  double dec_scz = dec_ps; // DEC of spacecraft Z axis

  // Open input ebounds extension, used for apparent energy bins.
  std::auto_ptr<const tip::Table> ebounds_ext(tip::IFileSvc::instance().readTable(m_data_dir + "PHA1.pha", "EBOUNDS"));

  // Read the detchans keyword. This determines the number of channels used for apparent energy.
  int detchans = 0;
  ebounds_ext->getHeader()["DETCHANS"].get(detchans);

  // Make sure there are at least detchans channels in the input ebounds. This is just a basic sanity check.
  tip::Index_t num_rec = ebounds_ext->getNumRecords();
  if (num_rec < detchans) throw std::runtime_error("test2: Channel number mismatch");
  std::vector<double> min_app_en(detchans);
  std::vector<double> max_app_en(detchans);

  tip::Index_t index = 0;
  for (tip::Table::ConstIterator ebounds_itor = ebounds_ext->begin(); ebounds_itor != ebounds_ext->end(); ++ebounds_itor) {
    (*ebounds_itor)["CHANNEL"].get(index);
    if (index > detchans) continue; // Skip any rows with channel numbers > the number of channels.
    // Warning: This assumes first channel is 1, but that is not necessarily true. Check TLMIN/TLMAX keywords
    --index; // Arrays start with 0, channels with 1.
    (*ebounds_itor)["E_MIN"].get(min_app_en[index]);
    (*ebounds_itor)["E_MAX"].get(max_app_en[index]);
    min_app_en[index] /= s_keV_per_MeV;
    max_app_en[index] /= s_keV_per_MeV;
  }
  // Add a check here to make sure all the channels were set. We can't compute response if any are missing.
  
  astro::SkyDir ps_dir(ra_ps, dec_ps);
  astro::SkyDir scz_dir(ra_scz, dec_scz);

  latResponse::Irfs * irfs = latResponse::irfsFactory().create("DC1::Front");
  // First get psf.
  latResponse::IPsf * psf = irfs->psf();

  // Compute angle, which should be 0.
  double theta = ps_dir.difference(scz_dir) * 180. / M_PI;

  double phi = 0.;

  // Create output response file from template:
  tip::IFileSvc::instance().createFile(file_name, m_data_dir + "LatResponseTemplate");

  // Open the response file:
  tip::Table * resp_table = tip::IFileSvc::instance().editTable(file_name, "MATRIX");

  resp_table->getHeader()["DETCHANS"].set(detchans);

  // Next get aeff.
  latResponse::IAeff * aeff = irfs->aeff();

  // And redistribution.
  latResponse::IEdisp * edisp = irfs->edisp();

  tip::Table::Iterator out_itor = resp_table->begin();

  // Number of true energy channels is not arbitrary, but is taken from the true energy binning info obtained above.
  int num_true_chan = num_bins;

  // Arrays used to write f_chan and n_chan columns, respectively.
  std::vector<int> f_chan(1, 1);
  std::vector<int> n_chan(1, detchans);
  for (long true_en_idx = 0; true_en_idx < num_true_chan; ++true_en_idx, ++out_itor) {
    double true_en = binner.getInterval(true_en_idx).midpoint();
    double aeff_val = aeff->value(true_en, theta, phi);
    double int_psf_val = psf->angularIntegral(true_en, theta, phi, radius);

    // Populate response vector.
    std::vector<double> response;
    for (index = 0; index < detchans; ++index) {
      response.push_back(aeff_val * edisp->integral(min_app_en[index], max_app_en[index], true_en, theta, phi) * int_psf_val);
    }

    // Write response to file, using keV.
    (*out_itor)["ENERG_LO"].set(s_keV_per_MeV * binner.getInterval(true_en_idx).begin());
    (*out_itor)["ENERG_HI"].set(s_keV_per_MeV * binner.getInterval(true_en_idx).end());
    (*out_itor)["N_GRP"].set(1);
    (*out_itor)["F_CHAN"].set(f_chan);
    (*out_itor)["N_CHAN"].set(n_chan);
    (*out_itor)["MATRIX"].set(response);
  }
  
  // Copy input ebounds extension to the output.
  tip::Table * out_ebounds = tip::IFileSvc::instance().editTable(file_name, "EBOUNDS");

  // Set detchans explicitly.
  out_ebounds->getHeader()["DETCHANS"].set(detchans);

  out_ebounds->setNumRecords(num_rec);

  tip::Table::ConstIterator in_itor = ebounds_ext->begin();
  for (out_itor = out_ebounds->begin(); out_itor != out_ebounds->end(); ++in_itor, ++out_itor) {
    *out_itor = *in_itor;
  }

  delete out_ebounds;
  delete resp_table;
  delete irfs;
}

// In this example. "true" energy comes from bin definition file.
// Also, the FT2 file is read and a histogram in time as a function of angle is created.
void RspGenTestApp::test3() {
  using namespace evtbin;

  double ra_ps = 120.; // RA of point source
  double dec_ps = 30.; // DEC of point source
  astro::SkyDir ps_pos(ra_ps, dec_ps);

  // Open the sc data file.
  std::auto_ptr<const tip::Table> sc_data(tip::IFileSvc::instance().readTable(m_data_dir + "D2.fits", "Ext1"));

  // Set up a histogram to hold the binned differential exposure (theta vs. DeltaT).
  Hist1D diff_exp(LinearBinner(0., 60., 5.));

  double total_exposure = 0;

  // Read SC Z positions, bin them into a histogram:
  for (tip::Table::ConstIterator itor = sc_data->begin(); itor != sc_data->end(); ++itor) {
    // Get size of interval.
    double delta_t = (*itor)["LIVETIME"].get();
    
    // Get SC coordinates.
    double ra_scz = (*itor)["RA_SCZ"].get();
    double dec_scz = (*itor)["DEC_SCZ"].get();
    astro::SkyDir scz_pos(ra_scz, dec_scz);

    // Compute inclination angle from the source position to the sc.
    double theta = ps_pos.difference(scz_pos) * 180. / M_PI;

    // Bin this angle into the histogram.
    diff_exp.fillBin(theta, delta_t);

    total_exposure += delta_t;
  }

  // Make sure small differences will be printed correctly.
  std::cout.precision(24);

#ifdef foo
  std::cout << "***************** histogram values ***************" << std::endl;
  for (int ii = 0; ii < 12; ++ii)
    std::cout << diff_exp[ii]/(2.5 + ii * 5.) << std::endl;
  std::cout << "***************** histogram values ***************" << std::endl;
#endif

  // Create interval container for user defined bin intervals.
  OrderedBinner::IntervalCont_t intervals;

  // Open the data file.
  std::auto_ptr<const tip::Table> table(tip::IFileSvc::instance().readTable(m_data_dir + "StdEnergyBin.fits", "ENERGYBINS"));

  // Iterate over the file, saving the relevant values into the interval array.
  for (tip::Table::ConstIterator itor = table->begin(); itor != table->end(); ++itor) {
    intervals.push_back(Binner::Interval((*itor)["START_BIN"].get(), (*itor)["STOP_BIN"].get()));
  }

  // Create binner from these intervals.
  OrderedBinner binner(intervals);
 
  long num_bins = binner.getNumBins();

  // Open input pha file.
  std::auto_ptr<const tip::Table> ebounds_ext(tip::IFileSvc::instance().readTable(m_data_dir + "PHA1.pha", "EBOUNDS"));

  // Read the detchans keyword. This determines the number of channels used for apparent energy.
  int detchans = 0;
  ebounds_ext->getHeader()["DETCHANS"].get(detchans);

  // Make sure there are at least detchans channels in the input ebounds. This is just a basic sanity check.
  tip::Index_t num_rec = ebounds_ext->getNumRecords();
  if (num_rec < detchans) throw std::runtime_error("test3: Channel number mismatch");
  std::vector<double> min_app_en(detchans);
  std::vector<double> max_app_en(detchans);

  tip::Index_t index = 0;
  for (tip::Table::ConstIterator ebounds_itor = ebounds_ext->begin(); ebounds_itor != ebounds_ext->end(); ++ebounds_itor) {
    (*ebounds_itor)["CHANNEL"].get(index);
    if (index > detchans) continue; // Skip any rows with channel numbers > the number of channels.
    // Warning: This assumes first channel is 1, but that is not necessarily true. Check TLMIN/TLMAX keywords
    --index; // Arrays start with 0, channels with 1.
    (*ebounds_itor)["E_MIN"].get(min_app_en[index]);
    (*ebounds_itor)["E_MAX"].get(max_app_en[index]);
    min_app_en[index] /= s_keV_per_MeV;
    max_app_en[index] /= s_keV_per_MeV;
  }
  // Add a check here to make sure all the channels were set. We can't compute response if any are missing.
  
  latResponse::Irfs * irfs = latResponse::irfsFactory().create("DC1::Front");
  // First get psf.
  latResponse::IPsf * psf = irfs->psf();

  // Theta varies over the histogram now.
  // double theta = ps_dir.difference(scz_dir) * 180. / M_PI;

  double phi = 0.;
  double radius = 0.1;

  // Create output response file from template:
  tip::IFileSvc::instance().createFile("test_response3.rsp", m_data_dir + "LatResponseTemplate");

  // Open the response file:
  tip::Table * resp_table = tip::IFileSvc::instance().editTable("test_response3.rsp", "MATRIX");

  resp_table->getHeader()["DETCHANS"].set(detchans);

  // Next get aeff.
  latResponse::IAeff * aeff = irfs->aeff();

  // And redistribution.
  latResponse::IEdisp * edisp = irfs->edisp();

  tip::Table::Iterator out_itor = resp_table->begin();

  // Arbitrarily set the number of channels used for "true" energy dimension.
  int num_true_chan = num_bins;

  // Arrays used to write f_chan and n_chan columns, respectively.
  std::vector<int> f_chan(1, 1);
  std::vector<int> n_chan(1, detchans);

  // Iterate over the bins of the histogram.
  const Binner * theta_bins = diff_exp.getBinners()[0];
  long num_theta_bins = theta_bins->getNumBins();

  for (long true_en_idx = 0; true_en_idx < num_true_chan; ++true_en_idx, ++out_itor) {
    double true_en = binner.getInterval(true_en_idx).midpoint();

    // Populate response vector.
    std::vector<double> response(detchans, 0.);

    // Integrate over binned angle-dependent differential exposure.
    for (long theta_bin = 0; theta_bin < num_theta_bins; ++theta_bin) {
      double theta = theta_bins->getInterval(theta_bin).midpoint();
      double aeff_val = aeff->value(true_en, theta, phi);
      double int_psf_val = psf->angularIntegral(true_en, theta, phi, radius);
  
      for (index = 0; index < detchans; ++index) {
        response[index] += diff_exp[theta_bin] / total_exposure * aeff_val * edisp->integral(min_app_en[index], max_app_en[index], true_en, theta, phi) * int_psf_val;
      }
  
      // Write response to file, using keV.
      (*out_itor)["ENERG_LO"].set(s_keV_per_MeV * binner.getInterval(true_en_idx).begin());
      (*out_itor)["ENERG_HI"].set(s_keV_per_MeV * binner.getInterval(true_en_idx).end());
      (*out_itor)["N_GRP"].set(1);
      (*out_itor)["F_CHAN"].set(f_chan);
      (*out_itor)["N_CHAN"].set(n_chan);
      (*out_itor)["MATRIX"].set(response);
    }
  }
  
  // Copy ebounds extension from input to output.
  tip::Table * out_ebounds = tip::IFileSvc::instance().editTable("test_response3.rsp", "EBOUNDS");

  // Set detchans explicitly.
  out_ebounds->getHeader()["DETCHANS"].set(detchans);

  out_ebounds->setNumRecords(num_rec);

  tip::Table::ConstIterator in_itor = ebounds_ext->begin();
  for (out_itor = out_ebounds->begin(); out_itor != out_ebounds->end(); ++in_itor, ++out_itor) {
    *out_itor = *in_itor;
  }

  delete out_ebounds;
  delete resp_table;
  delete irfs;
}

// Test GrbResponse class constructors and compute method.
void RspGenTestApp::test4() {
  using namespace rspgen;

  try {
    // This test assumes there was a burst at (22., -25.), at t = 105. seconds.

    // Get spacecraft data.
    std::auto_ptr<const tip::Table> sc_table(tip::IFileSvc::instance().readTable(m_data_dir + "D2.fits", "Ext1"));

    // Get object for interpolating values from the table.
    tip::LinearInterp sc_record(sc_table->begin(), sc_table->end());

    // Interpolate values for a burst at 105. seconds.
    sc_record.interpolate("START", 105.);

    // Compute inclination angle from burst RA and DEC and spacecraft pointing.
    double theta = astro::SkyDir(22., -25.).difference(astro::SkyDir(sc_record.get("RA_SCZ"), sc_record.get("DEC_SCZ")))*180./M_PI;


    // Confirm that this value is correct.
    if (23.650202751159668 != sc_record.get("RA_SCZ")) {
      m_failed = true;
      std::cerr << "Unexpected: in test4, interpolated RA_SCZ was " << sc_record.get("RA_SCZ") << ", not 23.650202751159668"
        << std::endl;
    }


    // Get irfs object from latResponse.
    std::auto_ptr<latResponse::Irfs> irfs(latResponse::irfsFactory().create("DC1::Front"));


    // Create window object for psf integration, a circle of radius 1.4 degrees.
    CircularWindow window(1.4);


    // Get input ebounds extension.
    std::auto_ptr<const tip::Table> in_ebounds(tip::IFileSvc::instance().readTable(m_data_dir + "PHA1.pha", "EBOUNDS"));

    // Get number of channels currently in use.
    int detchans = 0;
    in_ebounds->getHeader()["DETCHANS"].get(detchans);
    
    // Get apparent energy binner from ebounds extension.
    int index = 0;
    evtbin::OrderedBinner::IntervalCont_t app_intervals(detchans);
    for (tip::Table::ConstIterator itor = in_ebounds->begin(); itor != in_ebounds->end() && index < detchans; ++itor, ++index)
      app_intervals[index] = evtbin::Binner::Interval((*itor)["E_MIN"].get()/s_keV_per_MeV, (*itor)["E_MAX"].get()/s_keV_per_MeV);

    // Create apparent energy binner.
    evtbin::OrderedBinner app_en_binner(app_intervals);


    // Process bin definition file to produce true energy bins.
    std::auto_ptr<const tip::Table> true_en(tip::IFileSvc::instance().readTable(m_data_dir + "StdEnergyBin.fits", "ENERGYBINS"));

    // Create object to hold the intervals in the bin definition file.
    evtbin::OrderedBinner::IntervalCont_t true_intervals(true_en->getNumRecords());

    // Read true energy bin definitions into interval object.
    index = 0;
    for (tip::Table::ConstIterator itor = true_en->begin(); itor != true_en->end(); ++itor, ++index)
      true_intervals[index] = evtbin::Binner::Interval((*itor)["START_BIN"].get(), (*itor)["STOP_BIN"].get());

    // Create a binner for true energy.
    evtbin::OrderedBinner true_en_binner(true_intervals);

    // Create response object for burst, using the first constructor.
    GrbResponse resp(theta, &true_en_binner, &app_en_binner, irfs.get(), &window);

    // Sanity check: just compute one response at 137. MeV.
    std::vector<double> resp_slice(detchans, 0.);
    resp.compute(137., resp_slice);
    
    // Use the second constructor, and test that its results are the same.
    // RA, DEC, t, radius, response type, pha file, FT2 file, energy bin def file
    GrbResponse resp2(22., -25., 105., 1.4, "DC1::Front", m_data_dir + "PHA1.pha", m_data_dir + "D2.fits", &true_en_binner);

    // Sanity check: just compute one response at 137. MeV.
    std::vector<double> resp_slice2(detchans, 0.);
    resp2.compute(137., resp_slice2);

    // Make sure the two response objects agree with their computations.
    if (resp_slice != resp_slice2) {
      m_failed = true;
      std::cerr << "Unexpected: GrbResponse objects constructed differently from same data give different results" << std::endl;
    }

    // Look for at least one non-zero value in the response computation.
    std::vector<double>::iterator resp_itor;
    for (resp_itor = resp_slice.begin(); resp_itor != resp_slice.end(); ++resp_itor)
      if (0. != *resp_itor) break;

    if (resp_slice.end() == resp_itor) {
      m_failed = true;
      std::cerr << "Unexpected: GrbResponse computed an all zero response slice at 137. MeV" << std::endl;
    }

    // Write output rsp file.
    resp2.writeOutput("test_rspgen", "test_response4.rsp", m_data_dir + "LatResponseTemplate");

  } catch (const std::exception & x) {
    m_failed = true;
    std::cerr << "Unexpected: test4 caught " << typeid(x).name() << ": " << x.what() << std::endl;
  }

}

// Verify that test2 produces same result as GrbResponse class in test4.
void RspGenTestApp::test5() {
  using namespace rspgen;

  try {
    // Repeat test2 using test4 parameters.
    test2(22., -25., 1.4, "test_response5.rsp");
  } catch (const std::exception & x) {
    m_failed = true;
    std::cerr << "Unexpected: test5 caught " << typeid(x).name() << ": " << x.what() << std::endl;
  }

}

// Test application class for GrbResponse case.
void RspGenTestApp::test6() {
  using namespace rspgen;

  try {
    RspGenApp app;

    st_app::AppParGroup & pars(getParGroup("rspgen"));

    // Set parameters "by hand"
    pars["respalg"] = "GRB";
    pars["specfile"] = m_data_dir + "PHA1.pha";
    pars["scfile"] = m_data_dir + "D2.fits";
    pars["outfile"] = "test_response6.rsp";
    pars["ra"] = 22.;
    pars["dec"] = -27.;
    pars["time"] = 105.;
    pars["psfradius"] = 1.4;
    pars["resptype"] = "DC1::Front";
    pars["resptpl"] = "";
    pars["energybinalg"] = "FILE";
    pars["energybinfile"] = m_data_dir + "StdEnergyBin.fits";

    // And writing the output.
    app.writeResponse(pars);

  } catch (const std::exception & x) {
    m_failed = true;
    std::cerr << "Unexpected: test6 caught " << typeid(x).name() << ": " << x.what() << std::endl;
  }

}

// Test PointResponse class constructors and compute method. Parameters are such that
// this test's output should be identical to test3's output.
void RspGenTestApp::test7() {
  using namespace rspgen;

  try {
    // Create a binner for true energy.
    std::auto_ptr<evtbin::Binner> true_en_binner(createStdBinner());

    // Construct a steady point source response for the given RA, DEC, thetabins.
    // RA, DEC, theta_cut, theta_bin_size, radius, response type, pha file, FT2 file, energy bin def file.
    PointResponse resp(120., 30., 60., 5., .1, "DC1::Front", m_data_dir + "PHA1.pha", m_data_dir + "D2.fits",
      true_en_binner.get());

    // Sanity check: just compute one response at 137. MeV.
    std::vector<double> resp_slice;
    resp.compute(137., resp_slice);

    // Look for at least one non-zero value in the response computation.
    std::vector<double>::iterator resp_itor;
    for (resp_itor = resp_slice.begin(); resp_itor != resp_slice.end(); ++resp_itor)
      if (0. != *resp_itor) break;

    if (resp_slice.end() == resp_itor) {
      m_failed = true;
      std::cerr << "Unexpected: PointResponse computed an all zero response slice at 137. MeV" << std::endl;
    }

    // Write output rsp file.
    resp.writeOutput("test_rspgen", "test_response7.rsp", m_data_dir + "LatResponseTemplate");

  } catch (const std::exception & x) {
    m_failed = true;
    std::cerr << "Unexpected: test7 caught " << typeid(x).name() << ": " << x.what() << std::endl;
  }

}

// Test application class for PointResponse case.
void RspGenTestApp::test8() {
  using namespace rspgen;

  try {
    RspGenApp app;

    st_app::AppParGroup & pars(getParGroup("rspgen"));

    // Set parameters "by hand"
    pars["respalg"] = "PS";
    pars["specfile"] = m_data_dir + "PHA1.pha";
    pars["scfile"] = m_data_dir + "D2.fits";
    pars["outfile"] = "test_response8.rsp";
    pars["ra"] = 120.;
    pars["dec"] = 30.;
    pars["thetacut"] = 60.;
    pars["thetabinsize"] = 5.;
    pars["psfradius"] = .1;
    pars["resptype"] = "DC1::Front";
    pars["resptpl"] = "";
    pars["energybinalg"] = "FILE";
    pars["energybinfile"] = m_data_dir + "StdEnergyBin.fits";

    // And writing the output.
    app.writeResponse(pars);

  } catch (const std::exception & x) {
    m_failed = true;
    std::cerr << "Unexpected: test8 caught " << typeid(x).name() << ": " << x.what() << std::endl;
  }

}

evtbin::Binner * RspGenTestApp::createStdBinner() {
  // Process bin definition file to produce true energy bins.
  std::auto_ptr<const tip::Table> true_en(tip::IFileSvc::instance().readTable(m_data_dir + "StdEnergyBin.fits", "ENERGYBINS"));

  // Create object to hold the intervals in the bin definition file.
  evtbin::OrderedBinner::IntervalCont_t true_intervals(true_en->getNumRecords());

  // Read true energy bin definitions into interval object.
  int index = 0;
  for (tip::Table::ConstIterator itor = true_en->begin(); itor != true_en->end(); ++itor, ++index)
    true_intervals[index] = evtbin::Binner::Interval((*itor)["START_BIN"].get(), (*itor)["STOP_BIN"].get());

  // Create a binner for true energy.
  return new evtbin::OrderedBinner(true_intervals);
}

// Factory object to create this test executable.
st_app::StAppFactory<RspGenTestApp> g_factory;
