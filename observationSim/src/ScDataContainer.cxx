/**
 * @file ScDataContainer.cxx
 * @brief Implementation for class that keeps track of events and when they
 * get written to a FITS file.
 * @author J. Chiang
 * $Header$
 */

#include <sstream>
#include <stdexcept>

#include "CLHEP/Geometry/Vector3D.h"

#include "tip/IFileSvc.h"
#include "tip/Image.h"
#include "tip/Table.h"

#include "st_facilities/FitsUtil.h"
#include "st_facilities/Util.h"

#include "astro/EarthCoordinate.h"

#include "flux/EventSource.h"

#include "observationSim/EventContainer.h"
#include "observationSim/ScDataContainer.h"

namespace observationSim {

ScDataContainer::~ScDataContainer() {
   if (m_scData.size() > 0) writeScData();
}

void ScDataContainer::init() {
   m_scData.clear();

   char * root_path = std::getenv("OBSERVATIONSIMROOT");
   if (root_path != 0) {
      m_ftTemplate = std::string(root_path) + "/data/ft2.tpl";
   } else {
      throw std::runtime_error(std::string("Environment variable ") 
                               + "OBSERVATIONSIMROOT not set.");
   }
}

void ScDataContainer::addScData(EventSource *event, Spacecraft *spacecraft,
                                bool flush) {
   double time = event->time();
   addScData(time, spacecraft, flush);
}

void ScDataContainer::addScData(double time, Spacecraft * spacecraft, 
                                bool flush) {
   try {
      astro::SkyDir zAxis = spacecraft->zAxis(time);
      astro::SkyDir xAxis = spacecraft->xAxis(time);
      std::vector<double> scPosition;
      spacecraft->getScPosition(time, scPosition);
      double raZenith, decZenith;
      spacecraft->getZenith(time, raZenith, decZenith);
      double livetimeFrac = spacecraft->livetimeFrac(time);

      m_scData.push_back(ScData(time, zAxis.ra(), zAxis.dec(), 
                                spacecraft->EarthLon(time), 
                                spacecraft->EarthLat(time),
                                zAxis, xAxis, spacecraft->inSaa(time),
                                scPosition, raZenith, decZenith,
                                livetimeFrac));
   } catch (std::exception & eObj) {
      if (!st_facilities::Util::expectedException(eObj,"Time out of Range!")) {
         throw;
      }
   }
   if (flush || m_scData.size() >= m_maxNumEntries) writeScData();
}

void ScDataContainer::writeScData() {
   if (m_writeData) {
      std::string ft2File = outputFileName();
      tip::IFileSvc::instance().createFile(ft2File, m_ftTemplate);
      tip::Table * my_table = 
         tip::IFileSvc::instance().editTable(ft2File, "Ext1");
      int npts = m_scData.size();
      my_table->setNumRecords(npts);
      tip::Table::Iterator it = my_table->begin();
      tip::Table::Record & row = *it;
      std::vector<ScData>::const_iterator sc = m_scData.begin();
      double start_time = m_scData.begin()->time();
      double stop_time = 2.*m_scData[npts-1].time() - m_scData[npts-2].time();
      for ( ; it != my_table->end(), sc != m_scData.end(); ++it, ++sc) {
         row["start"].set(sc->time());
         double interval;
         if (sc+1 != m_scData.end()) {
            row["stop"].set((sc+1)->time());
            interval = (sc+1)->time() - sc->time();
         } else {
            row["stop"].set(stop_time);
            interval = stop_time - sc->time();
         }
         row["livetime"].set(sc->livetimeFrac()*interval);
         row["deadtime"].set(interval*(1. - sc->livetimeFrac()));
         row["lat_geo"].set(sc->lat());
         row["lon_geo"].set(sc->lon());
         row["ra_scz"].set(sc->zAxis().ra());
         row["dec_scz"].set(sc->zAxis().dec());
         row["ra_scx"].set(sc->xAxis().ra());
         row["dec_scx"].set(sc->xAxis().dec());
         row["sc_position"].set(sc->position());
         row["ra_zenith"].set(sc->raZenith());
         row["dec_zenith"].set(sc->decZenith());
         row["in_saa"].set(sc->inSaa());
         if (sc->inSaa()) {
            row["livetime"].set(0);
            row["deadtime"].set(interval);
         }
      }
      writeDateKeywords(my_table, start_time, stop_time);
      delete my_table;

// Take care of date keywords in primary header.
      tip::Image * phdu = tip::IFileSvc::instance().editImage(ft2File, "");
      writeDateKeywords(phdu, start_time, stop_time);
      delete phdu;

      st_facilities::FitsUtil::writeChecksums(ft2File);
// Update the m_fileNum index.
      m_fileNum++;
   }

// Flush the buffer...
   m_scData.clear();
}

} // namespace observationSim
