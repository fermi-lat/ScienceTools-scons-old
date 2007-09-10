/** \file EventTimeHandler.cxx
    \brief Implementation of EventTimeHandler class.
    \authors Masaharu Hirayama, GSSC
             James Peachey, HEASARC/GSSC
*/
#include "timeSystem/EventTimeHandler.h"

#include "timeSystem/AbsoluteTime.h"
#include "timeSystem/BaryTimeComputer.h"

#include <cmath>
#include <sstream>
#include <stdexcept>

extern "C" {
#include "bary.h"
}

namespace timeSystem {

  EventTimeHandler::EventTimeHandler(tip::Table & table, double position_tolerance):
    m_table(&table), m_bary_time(false), m_position_tolerance(position_tolerance), m_ra_nom(0.), m_dec_nom(0.),
    m_computer(BaryTimeComputer::getComputer()) {
    // Get table header.
    const tip::Header & header(m_table->getHeader());

    // Check TELESCOP keyword.
    std::string telescope;
    header["TELESCOP"].get(telescope);
    for (std::string::iterator itor = telescope.begin(); itor != telescope.end(); ++itor) *itor = std::toupper(*itor);
    if (telescope != "GLAST") throw std::runtime_error("Only GLAST supported for now");
    // TODO: Use dicision-making chain to support multiple missions.

    // Set to the first record in the table.
    setFirstRecord();

    // Check whether times in this table are already barycentered.
    std::string time_ref;
    header["TIMEREF"].get(time_ref);
    for (std::string::iterator itor = time_ref.begin(); itor != time_ref.end(); ++itor) *itor = std::toupper(*itor);
    m_bary_time = ("SOLARSYSTEM" == time_ref);

    // Get RA_NOM and DEC_NOM header keywords, if times in this table are barycentered.
    if (m_bary_time) {
      double ra_file;
      double dec_file;
      try {
        header["RA_NOM"].get(ra_file);
        header["DEC_NOM"].get(dec_file);
      } catch (const std::exception &) {
        throw std::runtime_error("Could not find RA_NOM or DEC_NOM header keyword in a barycentered event file.");
      }
      m_ra_nom = ra_file;
      m_dec_nom = dec_file;
    }

    // Pre-compute three vector version of RA_NOM and DEC_NOM.
    computeThreeVector(m_ra_nom, m_dec_nom, m_vect_nom);
  }

  EventTimeHandler::~EventTimeHandler() {}

  AbsoluteTime EventTimeHandler::readHeader(const std::string & keyword_name) {
    return readTime(m_table->getHeader(), keyword_name, false, 0., 0.);
  }
  
  AbsoluteTime EventTimeHandler::readHeader(const std::string & keyword_name, const double ra, const double dec) {
    if (m_bary_time) {
      // Check RA & Dec in argument list match the table header, if already barycentered.
      checkSkyPosition(ra, dec);

      // Read barycentric time and return it.
      return readTime(m_table->getHeader(), keyword_name, false, ra, dec);

    } else {
      // Delegate computation of barycenteric time and return the result.
      return readTime(m_table->getHeader(), keyword_name, true, ra, dec);
    }
  }

  AbsoluteTime EventTimeHandler::readColumn(const std::string & column_name) {
    return readTime(*m_record_itor, column_name, false, 0., 0.);
  }
  
  AbsoluteTime EventTimeHandler::readColumn(const std::string & column_name, const double ra, const double dec) {
    if (m_bary_time) {
      // Check RA & Dec in argument list match the table header, if already barycentered.
      checkSkyPosition(ra, dec);

      // Read barycentric time and return it.
      return readTime(*m_record_itor, column_name, false, ra, dec);

    } else {
      // Delegate computation of barycenteric time and return the result.
      return readTime(*m_record_itor, column_name, true, ra, dec);
    }
  }

  void EventTimeHandler::setFirstRecord() {
    m_record_itor = m_table->begin();
  }

  void EventTimeHandler::setNextRecord() {
    if (m_record_itor != m_table->end()) ++m_record_itor;
  }

  bool EventTimeHandler::isEndOfTable() const {
    return (m_record_itor == m_table->end());
  }

  tip::Header & EventTimeHandler::getHeader() const {
    return m_table->getHeader();
  }

  tip::TableRecord & EventTimeHandler::getCurrentRecord() const {
    return *m_record_itor;
  }

  void EventTimeHandler::computeBaryTime(const double ra, const double dec, const double sc_position[], AbsoluteTime & abs_time) const {
    m_computer.computeBaryTime(ra, dec, sc_position, abs_time);
  }

  double EventTimeHandler::computeInnerProduct(const double vect_x[], const double vect_y[]) const {
    return vect_x[0]*vect_y[0] + vect_x[1]*vect_y[1] + vect_x[2]*vect_y[2];
  }

  void EventTimeHandler::computeOuterProduct(const double vect_x[], const double vect_y[], double vect_z[]) const {
    vect_z[0] = vect_x[1]*vect_y[2] - vect_x[2]*vect_y[1];
    vect_z[1] = vect_x[2]*vect_y[0] - vect_x[0]*vect_y[2];
    vect_z[2] = vect_x[0]*vect_y[1] - vect_x[1]*vect_y[0];
  }

  void EventTimeHandler::computeThreeVector(const double ra, const double dec, double vect[]) const {
    vect[0] = std::cos(ra/RADEG) * std::cos(dec/RADEG);
    vect[1] = std::sin(ra/RADEG) * std::cos(dec/RADEG);
    vect[2] = std::sin(dec/RADEG);
  }

  void EventTimeHandler::checkSkyPosition(const double ra, const double dec) const {
    double source[3];
    computeThreeVector(ra, dec, source);

    double outer[3] = {0., 0., 0.};
    computeOuterProduct(source, m_vect_nom, outer);

    double separation_angle = std::asin(sqrt(computeInnerProduct(outer, outer))) * RADEG;

    if (separation_angle > m_position_tolerance) {
      std::ostringstream os;
      os << "Sky position for barycentric corrections (RA=" << ra << ", Dec=" << dec << 
        ") does not match RA_NOM (" << m_ra_nom << ") and DEC_NOM (" << m_dec_nom << ") in Event file.";
      throw std::runtime_error(os.str());
    }

  }
}
