#include "Likelihood/Function.h"
#include "Likelihood/Arg.h"

namespace Likelihood {
/** 
 * @class Gaussian
 *
 * @brief A Gaussian function
 *
 * @author J. Chiang
 *    
 * $Header$
 */
    
class Gaussian : public Function {
public:

   Gaussian(){m_init(0, -2, 1);}
   Gaussian(double Prefactor, double Mean, double Sigma)
      {m_init(Prefactor, Mean, Sigma);}

   double value(Arg &) const;

   double derivByParam(Arg &, const std::string &paramName) const;

   double integral(Arg &xmin, Arg &xmax) const;

private:

   void m_init(double Prefactor, double Mean, double Sigma);
   double m_erfcc(double x) const;

};

} // namespace Likelihood

