/**
 * @file Util.h
 * @brief Utilities for fitsGen apps.
 * @author J. Chiang
 *
 * $Header$
 */

#ifndef fitsGen_Util_h
#define fitsGen_Util_h

#include <string>

#include "astro/JulianDate.h"

namespace tip {
   class Table;
}

namespace fitsGen {

/**
 * @class Util
 * @brief Static function utilities for fitsGen applications.
 * @author J. Chiang
 *
 * $Header$
 */

class Util {

public:

   static void getFileNames(int iargc, char * argv[], std::string & rootFile,
                            std::string & fitsFile);

   static void writeDateKeywords(tip::Extension * table, double start_time,
                                 double stop_time, bool extension=true,
                                 const astro::JulianDate & mission_start
                                 =astro::JulianDate(2001, 1, 1, 0));

   static astro::JulianDate currentTime();

};

} // namespace fitsGen

#endif // fitsGen_Util_h
