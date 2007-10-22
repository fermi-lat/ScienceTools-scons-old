/**
 * @file LatSc.cxx
 * @brief Implementation of LatSc class.
 * @author J. Chiang
 *
 * $Header$
 */

#include "astro/EarthCoordinate.h"
#include "astro/PointingTransform.h"
#include "astro/GPS.h"

#include "LatSc.h"

namespace observationSim {

astro::SkyDir LatSc::zAxis(double time) {
   HepRotation rotationMatrix = InstrumentToCelestial(time);
   return astro::SkyDir(rotationMatrix(Hep3Vector(0, 0, 1)),
                        astro::SkyDir::EQUATORIAL);
}

astro::SkyDir LatSc::xAxis(double time) {
   HepRotation rotationMatrix = InstrumentToCelestial(time);
   return astro::SkyDir(rotationMatrix(Hep3Vector(1, 0, 0)),
                        astro::SkyDir::EQUATORIAL);
}

double LatSc::EarthLon(double time) {
   astro::GPS * gps(astro::GPS::instance());
   gps->time(time);
   return gps->lon();
}

double LatSc::EarthLat(double time) {
   astro::GPS * gps(astro::GPS::instance());
   gps->time(time);
   return gps->lat();
}

HepRotation LatSc::InstrumentToCelestial(double time) {
   astro::GPS * gps(astro::GPS::instance());
   gps->time(time);
   astro::PointingTransform transform(gps->zAxisDir(), gps->xAxisDir());
   return transform.localToCelestial();
}

bool LatSc::inSaa(double time) {
   if (::getenv("DISABLE_SAA")) {
      return false;
   }
   astro::EarthCoordinate earthCoord( EarthLat(time), EarthLon(time) );
   return earthCoord.insideSAA();
}

void LatSc::getScPosition(double time, std::vector<double> & position) {
   Hep3Vector pos = astro::GPS::instance()->position(time);
   position.clear();
// GPS returns the position in units of km, but FT2 wants meters so
// we multiply by 10^3.
   double mperkm(1e3);
   position.push_back(pos.x()*mperkm);
   position.push_back(pos.y()*mperkm);
   position.push_back(pos.z()*mperkm);
}

void LatSc::getZenith(double time, double & ra, double & dec) {
   astro::GPS * gps(astro::GPS::instance());
   gps->time(time);
   astro::SkyDir zenithDir(gps->zenithDir());
   ra = zenithDir.ra();
   dec = zenithDir.dec();
}

} // namespace observationSim
