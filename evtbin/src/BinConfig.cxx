/** \file BinConfig.cxx
    \brief Implementation of helper class which uses standard sets of parameters to configure binners for standard applications.
    \author James Peachey, HEASARC
*/
#include <memory>
#include <stdexcept>
#include <string>

#include "evtbin/BinConfig.h"
#include "evtbin/LinearBinner.h"
#include "evtbin/LogBinner.h"
#include "evtbin/OrderedBinner.h"

// Interactive parameter file access from st_app.
#include "st_app/AppParGroup.h"

// File access from tip.
#include "tip/IFileSvc.h"
// Table access from tip.
#include "tip/Table.h"

namespace evtbin {

  void BinConfig::energyParPrompt(st_app::AppParGroup & par_group) {
    parPrompt(par_group, "energybinalg", "energyfield", "emin", "emax", "deltaenergy", "enumbins", "energybinfile");
  }

  void BinConfig::timeParPrompt(st_app::AppParGroup & par_group) {
    parPrompt(par_group, "timebinalg", "timefield", "tstart", "tstop", "deltatime", "ntimebins", "timebinfile");
  }

  Binner * BinConfig::createEnergyBinner(const st_app::AppParGroup & par_group) const {
    return createBinner(par_group, "energybinalg", "energyfield", "emin", "emax", "deltaenergy", "enumbins", "energybinfile",
      "ENERGYBINS", "START_BIN", "STOP_BIN");
  }

  Binner * BinConfig::createTimeBinner(const st_app::AppParGroup & par_group) const {
    return createBinner(par_group, "timebinalg", "timefield", "tstart", "tstop", "deltatime", "ntimebins", "timebinfile",
      "TIMEBINS", "START_BIN", "STOP_BIN");
  }

  void BinConfig::parPrompt(st_app::AppParGroup & par_group, const std::string & alg, const std::string & in_field,
    const std::string & bin_begin, const std::string & bin_end, const std::string & bin_size, const std::string & num_bins,
    const std::string & bin_file) {
    // Determine the time binning algorithm.
    par_group.Prompt(alg);
    par_group.Prompt(in_field);
    if (0 == par_group[alg].Value().compare("LIN")) {
      // Get remaining parameters needed for linearly uniform interval binner.
      par_group.Prompt(bin_begin);
      par_group.Prompt(bin_end);
      par_group.Prompt(bin_size);
    } else if (0 == par_group[alg].Value().compare("LOG")) {
      // Get remaining parameters needed for logarithmically uniform interval binner.
      par_group.Prompt(bin_begin);
      par_group.Prompt(bin_end);
      par_group.Prompt(num_bins);
    } else if (0 == par_group[alg].Value().compare("FILE")) {
      // Get remaining parameters needed for user defined bins from a bin file.
      par_group.Prompt(bin_file);
    } else throw std::runtime_error(std::string("Unknown time binning algorithm ") + par_group[alg].Value());
  }

  Binner * BinConfig::createBinner(const st_app::AppParGroup & par_group, const std::string & alg,
    const std::string & in_field, const std::string & bin_begin, const std::string & bin_end, const std::string & bin_size,
    const std::string & num_bins, const std::string & bin_file, const std::string & bin_ext, const std::string & start_field,
    const std::string & stop_field) const {
    using namespace evtbin;

    Binner * binner = 0;

    if (0 == par_group[alg].Value().compare("LIN")) {
      binner = new LinearBinner(par_group[bin_begin], par_group[bin_end], par_group[bin_size], par_group[in_field]);
    } else if (0 == par_group[alg].Value().compare("LOG")) {
      binner = new LogBinner(par_group[bin_begin], par_group[bin_end], par_group[num_bins], par_group[in_field]);
    } else if (0 == par_group[alg].Value().compare("FILE")) {
      // Create interval container for user defined bin intervals.
      OrderedBinner::IntervalCont_t intervals;

      // Open the data file.
      std::auto_ptr<const tip::Table> table(tip::IFileSvc::instance().readTable(par_group[bin_file], bin_ext));

      // Iterate over the file, saving the relevant values into the interval array.
      for (tip::Table::ConstIterator itor = table->begin(); itor != table->end(); ++itor) {
        intervals.push_back(Binner::Interval((*itor)[start_field].get(), (*itor)[stop_field].get()));
      }

      // Create binner from these intervals.
      binner = new OrderedBinner(intervals, par_group[in_field]);

    } else throw std::runtime_error(std::string("Unknown time binning algorithm ") + par_group[alg].Value());

    return binner;
  }

}
