/** \file AbsoluteTime.cxx
    \brief Implementation of AbsoluteTime class.
    \authors Masaharu Hirayama, GSSC
             James Peachey, HEASARC/GSSC
*/
#include "st_stream/Stream.h"

#include "timeSystem/AbsoluteTime.h"
#include "timeSystem/Duration.h"
#include "timeSystem/ElapsedTime.h"
#include "timeSystem/TimeInterval.h"
#include "timeSystem/TimeRep.h"
#include "timeSystem/TimeSystem.h"

namespace timeSystem {

  AbsoluteTime::AbsoluteTime(const std::string & time_system_name, const Duration & origin, const Duration & time):
    m_time_system(&TimeSystem::getSystem(time_system_name)), m_time(origin, time) {}

  AbsoluteTime::AbsoluteTime(const TimeRep & rep): m_time_system(0), m_time() { *this = rep.getTime(); }

  AbsoluteTime AbsoluteTime::operator +(const ElapsedTime & elapsed_time) const { return elapsed_time + *this; }

  AbsoluteTime AbsoluteTime::operator -(const ElapsedTime & elapsed_time) const { return -elapsed_time + *this; }

  TimeInterval AbsoluteTime::operator -(const AbsoluteTime & time) const { return TimeInterval(time, *this); }

  bool AbsoluteTime::operator >(const AbsoluteTime & other) const {
    Moment other_time = m_time_system->convertFrom(*other.m_time_system, other.m_time);
    return m_time.second > other_time.second + m_time_system->computeTimeDifference(other_time.first, m_time.first);
  }

  bool AbsoluteTime::operator >=(const AbsoluteTime & other) const {
    Moment other_time = m_time_system->convertFrom(*other.m_time_system, other.m_time);
    return m_time.second >= other_time.second + m_time_system->computeTimeDifference(other_time.first, m_time.first);
  }

  bool AbsoluteTime::operator <(const AbsoluteTime & other) const {
    Moment other_time = m_time_system->convertFrom(*other.m_time_system, other.m_time);
    return m_time.second < other_time.second + m_time_system->computeTimeDifference(other_time.first, m_time.first);
  }

  bool AbsoluteTime::operator <=(const AbsoluteTime & other) const {
    Moment other_time = m_time_system->convertFrom(*other.m_time_system, other.m_time);
    return m_time.second <= other_time.second + m_time_system->computeTimeDifference(other_time.first, m_time.first);
  }

  bool AbsoluteTime::equivalentTo(const AbsoluteTime & other, const ElapsedTime & tolerance) const {
    return (*this > other ? (*this <= other + tolerance) : (other <= *this + tolerance));
  }

  void AbsoluteTime::getTime(TimeRep & rep) const { rep.set(m_time_system->getName(), m_time.first, m_time.second); }

  ElapsedTime AbsoluteTime::computeElapsedTime(const std::string & time_system_name, const AbsoluteTime & since) const {
    const TimeSystem & time_system(TimeSystem::getSystem(time_system_name));
    // Convert both times into the given time system.
    Moment minuend = time_system.convertFrom(*m_time_system, m_time);
    Moment subtrahend = time_system.convertFrom(*(since.m_time_system), since.m_time);

    // Subtract the subtahend from the minuend.
    return ElapsedTime(time_system_name, minuend.second - subtrahend.second
                                         + m_time_system->computeTimeDifference(minuend.first, subtrahend.first));
  }

  AbsoluteTime AbsoluteTime::computeAbsoluteTime(const std::string & time_system_name, const Duration & delta_t) const {
    const TimeSystem & time_system(TimeSystem::getSystem(time_system_name));
    // Convert this time to a corresponding time in time_system
    Moment time1 = time_system.convertFrom(*m_time_system, m_time);

    // Add delta_t in time_system.
    time1.second += delta_t;

    // Return this time expressed as a new absolute time in the input time system.
    return AbsoluteTime(time_system_name, time1.first, time1.second);
  }

  std::ostream & operator <<(std::ostream & os, const AbsoluteTime & time) {
    time.write(os);
    return os;
  }

  st_stream::OStream & operator <<(st_stream::OStream & os, const AbsoluteTime & time) {
    time.write(os);
    return os;
  }

}
