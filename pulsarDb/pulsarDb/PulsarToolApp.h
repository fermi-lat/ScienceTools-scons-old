/** \file PulsarToolApp.h
    \brief Declaration of base class for pulsar tool applications.
    \author Masaharu Hirayama, GSSC
            James Peachey, HEASARC/GSSC
*/
#ifndef pulsarDb_PulsarToolApp_h
#define pulsarDb_PulsarToolApp_h

#include <map>
#include <string>
#include <vector>

#include "pulsarDb/EphChooser.h"
#include "pulsarDb/EphComputer.h"
#include "pulsarDb/PulsarEph.h"
#include "pulsarDb/TimingModel.h"

#include "st_app/AppParGroup.h"
#include "st_app/StApp.h"

#include "timeSystem/AbsoluteTime.h"
#include "timeSystem/TimeRep.h"

#include "tip/Header.h"
#include "tip/Table.h"

namespace pulsarDb {

  class PulsarToolApp : public st_app::StApp {
    public:
      typedef std::vector<const tip::Table *> table_cont_type;

      enum TimeCorrectionMode_e {
        REQUIRED, ALLOWED, SUPPRESSED
      };

      PulsarToolApp();
      virtual ~PulsarToolApp() throw();
      virtual void run() = 0;

      virtual timeSystem::TimeRep * createTimeRep(const std::string & time_format, const std::string & time_system,
        const std::string & time_value, const tip::Header * header = 0) const;

      virtual timeSystem::TimeRep * createTimeRep(const std::string & input_time_format, const std::string & input_time_system,
        const std::string & time_value, std::string & output_time_format, std::string & output_time_system,
        const tip::Header * header = 0) const;

      void openEventFile(const st_app::AppParGroup & pars, bool read_only = true);

      void reserveOutputField(const std::string & field_name, const std::string & field_format);

      void defineTimeCorrectionMode(const std::string & mode_name, TimeCorrectionMode_e tcmode_bary, TimeCorrectionMode_e tcmode_bin,
        TimeCorrectionMode_e tcmode_pdot);

      void selectTimeCorrectionMode(const std::string & mode_name);

      void selectTimeCorrectionMode(const st_app::AppParGroup & pars);

      void initEphComputer(const st_app::AppParGroup & pars, const TimingModel & model, const EphChooser & chooser,
        const std::string & eph_style);

      void initEphComputer(const st_app::AppParGroup & pars, const TimingModel & model, const EphChooser & chooser);

      void initTimeCorrection(const st_app::AppParGroup & pars, bool guess_pdot);

      void initTimeCorrection(const st_app::AppParGroup & pars, bool guess_pdot, const std::string & str_origin);

      void initTimeCorrection(const st_app::AppParGroup & pars, bool guess_pdot, const timeSystem::AbsoluteTime & abs_origin);

      double computeElapsedSecond(const timeSystem::AbsoluteTime & abs_time);

      timeSystem::AbsoluteTime computeAbsoluteTime(double elapsed_time);

      void setFirstEvent();

      void setNextEvent();

      bool isEndOfEventList() const;

      timeSystem::AbsoluteTime getEventTime();

      // TODO: Accept data types other than double.
      void setFieldValue(const std::string & field_name, double field_value);

      timeSystem::AbsoluteTime getStartTime();

      timeSystem::AbsoluteTime getStopTime();

      EphComputer & getEphComputer() const;

    private:
      table_cont_type m_event_table_cont;
      table_cont_type m_gti_table_cont;
      std::string m_time_field;
      std::string m_gti_start_field;
      std::string m_gti_stop_field;
      std::vector<std::pair<std::string, std::string> > m_output_field_cont;
      std::map<const tip::Table *, timeSystem::TimeRep *> m_time_rep_dict;
      std::map<const tip::Table *, bool> m_need_bary_dict;
      const tip::Header * m_reference_header;
      EphComputer * m_computer;
      std::map<const std::string, TimeCorrectionMode_e> m_tcmode_dict_bary;
      std::map<const std::string, TimeCorrectionMode_e> m_tcmode_dict_bin;
      std::map<const std::string, TimeCorrectionMode_e> m_tcmode_dict_pdot;
      TimeCorrectionMode_e m_tcmode_bary;
      TimeCorrectionMode_e m_tcmode_bin;
      TimeCorrectionMode_e m_tcmode_pdot;
      bool m_request_bary;
      bool m_demod_bin;
      bool m_cancel_pdot;
      timeSystem::TimeRep * m_target_time_rep;

      table_cont_type::iterator m_table_itor;
      tip::Table::ConstIterator m_event_itor;

      // TODO: refactor MetRep to include functionality of this method and remove this method.
      timeSystem::TimeRep * createMetRep(const std::string & time_system, const timeSystem::AbsoluteTime & abs_reference) const;

      timeSystem::AbsoluteTime readTimeColumn(const tip::Table & table, tip::ConstTableRecord & record,
        const std::string & column_name, bool request_time_correction = false);

      timeSystem::AbsoluteTime computeTimeBoundary(bool request_start_time, bool request_time_correction);

      void setupEventTable(const tip::Table & table);

  };

}

#endif
