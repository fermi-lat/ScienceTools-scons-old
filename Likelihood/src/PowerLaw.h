#include "../Likelihood/Function.h"

namespace Likelihood {
/** 
 * @class PowerLaw
 *
 * @brief A power-law function
 *
 * @author J. Chiang
 *    
 * $Header$
 */
    
class PowerLaw : public Function {
public:

   PowerLaw(){m_init(0, -2, 1);};
   PowerLaw(double Prefactor, double Index, double Scale)
      {m_init(Prefactor, Index, Scale);};

   virtual double value(double) const;
   virtual double operator()(double x) const {return value(x);};
   virtual double derivByParam(double, const std::string &paramName) const;
   virtual double integral(double xmin, double xmax);

private:

   void m_init(double Prefactor, double Index, double Scale);

};

} // namespace Likelihood

