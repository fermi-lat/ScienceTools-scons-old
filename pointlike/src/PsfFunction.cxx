/** @file PsfFunction.cxx
    @brief Class to define psf function.

    $Header$
    */
#include "pointlike/PsfFunction.h"    

using namespace pointlike;

double PsfFunction::operator () (const astro::SkyDir & r, const astro::SkyDir & r_prime,
                            double sigma) 
{
    double u( 0.5*(r_prime() - r()).mag2()/sigma/sigma);
    return operator()(u);
}
double PsfFunction::operator ()(double u)const
{
    return m_norm*(u<100? pow(1+u/m_gamma, -m_gamma) : 0);

}

double PsfFunction::integral(double umax)const
{
    return 1.- pow(1.+umax/m_gamma, 1.-m_gamma);
}

double PsfFunction::integralSquare(double umax)const
{
    return m_norm*m_norm*m_gamma/(2.*m_gamma-1)*(1-pow(1+umax/m_gamma, 1-2*m_gamma));
}
