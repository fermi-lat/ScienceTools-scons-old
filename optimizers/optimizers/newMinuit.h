/**
 * @file newMinuit.h
 * @brief Interface to the new C++ version of Minuit
 * @author P. Nolan
 * $Header: 
 */

#ifndef optimizers_NEWMINUIT_H
#define optimizers_NEWMINUIT_H

#include <vector>
#include "optimizers/Optimizer.h"
#include "optimizers/Statistic.h"
#include "Minuit/FCNGradientBase.h"
#include "Minuit/MnStrategy.h"
#include "Minuit/MnUserParameterState.h"

namespace optimizers {

  /**
   * @class myFCN
   * @brief The function minimized by Minuit
   * @author P. Nolan
   Minuit provides a base class for the function to be minimized.
   This is the implementation using the Optimizer infrastructure.

   Q:  Would it be better to do this as a hidden class within newMinuit?
  */

  class myFCN : public FCNGradientBase {
  public:
    myFCN(Statistic &);
    virtual ~myFCN() {};
    virtual double up() const {return 0.5;}
    virtual double operator() (const std::vector<double> &) const;
    virtual std::vector<double> gradient(const std::vector<double> &) const;
  private:
    Statistic * m_stat;
  };

  /**
   * @class newMinuit
   * @brief Wrapper class for the Minuit optimizer from CERN
   * @author P. Nolan
   This class implements an Optimizer by using Minuit, a well-known
   package from CERN.  It uses only a few of Minuit's features.
   It uses only the Migrad and Hesse algorithms.  All variables are
   treates as bounded.  No user interaction is allowed.  The new
   C++ implementation of Minuit is used, which has no limits on the
   number of free parameters.  The older Fortran version of Minuit is
   well known in the HEP community.  It was developed at CERN over a
   span of about 30 years.
  */

  class newMinuit : public Optimizer {
  public:
    newMinuit(Statistic &);
    virtual ~newMinuit() {};
    void find_min(int verbose=0, double tole = 1e-3, int tolType = ABSOLUTE);
    void setMaxEval(int);
    void setStrategy(unsigned int strat = 2) {m_strategy=MnStrategy(strat);}
    void setMaxEval(unsigned int n) {m_maxEval=n;}
    double getDistance(void) const {return m_distance;};
    void hesse(int verbose = 0);
    virtual const std::vector<double> & getUncertainty(bool useBase = false);
  private:
    unsigned int m_maxEval;
    bool m_fitDone;
    myFCN m_FCN;
    double m_distance;
    MnStrategy m_strategy;
    MnUserParameterState m_userState;
  };

}
#endif
