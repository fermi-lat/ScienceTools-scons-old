/** @file PointSourceLikelihood.cxx

$Header$

*/

#include "pointlike/PointSourceLikelihood.h"
#include "skymaps/SpectralFunction.h"
#include "pointlike/LeastSquaresFitter.h"

#include "skymaps/BandBackground.h"
#include "skymaps/DiffuseFunction.h"
#include "skymaps/BinnedPhotonData.h"
#include "embed_python/Module.h"
#include "TMatrixD.h"
#include "pointlike/ConfidenceLevel.h"

#include <iostream>
#include <fstream>
#include <algorithm>
#include <iomanip>
#include <stdexcept>
#include <map>
#include <list>
using namespace pointlike;
using astro::SkyDir;
using skymaps::CompositeSkySpectrum;
using skymaps::BinnedPhotonData;
using skymaps::Background;
using skymaps::DiffuseFunction;
using skymaps::Band;



namespace {
    // the scale_factor used: 2.5 degree at level 6, approximately the 68% containment
    double s_TScut(2.);  // only combine energy bands

    double sqr(double x){return x*x;}

#ifdef MIN_DEBUG
    std::ofstream minf("lsurface.txt");
#endif
}

//  ----- static (class) variables -----
const skymaps::Background* PointSourceLikelihood::s_diffuse(0);

// manage energy range for selection of bands to fit 
double PointSourceLikelihood::s_emin(200.); 
double PointSourceLikelihood::s_emax(1e6);
void PointSourceLikelihood::set_energy_range(double emin, double emax){
    s_emin = emin; s_emax=emax;
}
void PointSourceLikelihood::get_energy_range(double& emin, double& emax){
    emin = s_emin; emax=s_emax;
}

double PointSourceLikelihood::s_maxROI(180);
void   PointSourceLikelihood::set_maxROI(double r){s_maxROI=r;}
double PointSourceLikelihood::maxROI(){return s_maxROI;}

double PointSourceLikelihood::s_minROI(0.);
void   PointSourceLikelihood::set_minROI(double r){s_minROI=r;}
double PointSourceLikelihood::minROI(){return s_minROI;}

double PointSourceLikelihood::s_maxSig(0.25);
void   PointSourceLikelihood::set_maxSig(double r) {s_maxSig=r;}
double PointSourceLikelihood::maxSig(){return s_maxSig;}

double PointSourceLikelihood::set_min_alpha(double a){
    double r(s_minalpha); s_minalpha= a; return r;
}

double PointSourceLikelihood::s_minalpha(0.01);


int    PointSourceLikelihood::s_skip1(0);
int    PointSourceLikelihood::s_skip2(8);
int    PointSourceLikelihood::s_itermax(1);
double PointSourceLikelihood::s_TSmin(5.0);

int    PointSourceLikelihood::s_verbose(0);
void PointSourceLikelihood::set_verbose(bool verbosity){s_verbose=verbosity;}
bool PointSourceLikelihood::verbose(){return s_verbose;}

double PointSourceLikelihood::s_maxstep(0.25);  // if calculated step is larger then this (deg), abort localization

int  PointSourceLikelihood::s_merge(1); 
void PointSourceLikelihood::set_merge(bool merge){s_merge=merge;}
bool PointSourceLikelihood::merge(){return s_merge!=0;}

// option to perform least squares fit to log likelihood surface after localization
int  PointSourceLikelihood::s_fitlsq(0);  // default off
void PointSourceLikelihood::set_fitlsq(bool fit){s_fitlsq=fit;}
bool PointSourceLikelihood::fitlsq(){return s_fitlsq!=0;}

int  PointSourceLikelihood::s_conf(0);  // default off
void PointSourceLikelihood::set_conf(bool fit){s_conf=fit;}
bool PointSourceLikelihood::conf(){return s_conf!=0;}

void PointSourceLikelihood::setParameters(const embed_python::Module& par)
{
    static std::string prefix("PointSourceLikelihood.");

    par.getValue(prefix+"emin",     s_emin, s_emin);
    par.getValue(prefix+"emax",     s_emax, s_emax);
    par.getValue(prefix+"minalpha", s_minalpha, s_minalpha);
    par.getValue(prefix+"minROI",   s_minROI, s_minROI);
    par.getValue(prefix+"maxROI",   s_maxROI, s_maxROI);
    par.getValue(prefix+"maxSig",   s_maxSig, s_maxSig);

    par.getValue(prefix+"skip1",    s_skip1, s_skip1);
    par.getValue(prefix+"skip2",    s_skip2, s_skip2);
    par.getValue(prefix+"itermax",  s_itermax, s_itermax);
    par.getValue(prefix+"TSmin",    s_TSmin, s_TSmin);
    par.getValue(prefix+"verbose",  s_verbose, s_verbose);
    par.getValue(prefix+"maxstep",  s_maxstep, s_maxstep); // override with global
    par.getValue("verbose",  s_verbose, s_verbose); // override with global

    par.getValue(prefix+"merge",    s_merge, s_merge); // merge Bands with same nside, sigma
    par.getValue(prefix+"fitlsq",    s_fitlsq, s_fitlsq); // modify auto least squares
    par.getValue(prefix+"conf", s_conf, s_conf);

    int extended(false);
    par.getValue("extended_likelihood", extended, extended);
    SimpleLikelihood::enable_extended_likelihood(extended!=0);

    // needed by SimpleLikelihood
    double umax(SimpleLikelihood::defaultUmax());
    par.getValue(prefix+"umax", umax, umax);
    SimpleLikelihood::setDefaultUmax(umax);

    double tolerance(SimpleLikelihood::tolerance());
    par.getValue("Diffuse.tolerance",  tolerance, tolerance);
    SimpleLikelihood::setTolerance(tolerance);
    std::string diffusefile;
    par.getValue("Diffuse.file", diffusefile);
    double exposure(1.0);
    par.getValue("Diffuse.exposure", exposure);
    int interpolate(0);
    par.getValue("interpolate", interpolate, interpolate);

    double flux(1.5e-5), index(2.1);
    std::string ltfile,isofile;
    par.getValue("Isotropic.flux", flux, flux);
    par.getValue("Isotropic.index", index, index);
    par.getValue("Isotropic.file",isofile,isofile);

    par.getValue("Exposure.livetimefile", ltfile);
    std::string irf_name("P6_v1_diff");
    par.getValue("Exposure.IRF", irf_name, irf_name);

    if( ! diffusefile.empty()) {
        if( ltfile.empty() ) {

            set_background(new Background(
                *new DiffuseFunction(diffusefile, interpolate!=0), exposure) );

            std::cout << "Using diffuse definition "<< diffusefile 
                << " with exposure factor " << exposure << std::endl;
        }else{
            // combine all components in better Background ctor
            const Background* bg = new Background(irf_name, ltfile, diffusefile, isofile);
            set_background(bg);

        }
    }


}
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/* @class Iterator
Special iterator which skips pass Bands with a psf width which is too large
this should assist in localizing and calculating TS maps
The function set_maxSig determines the maximum width in degrees
*/
class Iterator {

public:

    ///! @brief ctor to make new special iterator
    ///! @param it first band in PSL (use begin())
    ///! @param end past last band in PSL (use end())
    Iterator(PointSourceLikelihood::const_iterator it, PointSourceLikelihood::const_iterator end)
        :m_it(it),
        m_end(end)
    {
        if((*m_it)->sigma()>=PointSourceLikelihood::maxSig()*M_PI/180.)
            ++(*this);
    }

    ///! @brief operator dereference
    SimpleLikelihood* operator*() const {return *m_it;}

    ///! @brief operator default increment
    PointSourceLikelihood::const_iterator operator++()
    {
        ++m_it;
        while(m_it!=m_end) {
            if((*m_it)->sigma()<PointSourceLikelihood::maxSig()*M_PI/180.)
                break;
            ++m_it;
        }
        return m_it;
    }

    ///! @brief operator comparison for end of PSL list
    bool operator!=(const PointSourceLikelihood::const_iterator& other) {return other!=m_it;}

private:
    PointSourceLikelihood::const_iterator m_it;
    PointSourceLikelihood::const_iterator m_end;
};

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PointSourceLikelihood::PointSourceLikelihood(
    const BinnedPhotonData& data,
    std::string name,
    const SkyDir& dir)
    : m_name(name)
    , m_dir(dir)
    , m_out(&std::cout)
    , m_background(0)
{

    if( s_diffuse !=0){
        m_background = new skymaps::CompositeSkySpectrum(s_diffuse);
    }else {
        // may not be valid?
        m_background = 0; //new skymaps::CompositeSkySpectrum();
    }
    setup( data);
}



void PointSourceLikelihood::setup( const skymaps::BinnedPhotonData& data )
{
    using skymaps::BandBackground;
    // select list for inclusion
    std::list<std::pair<const Band*,bool> > bands;
    for( skymaps::BinnedPhotonData::const_iterator bit = data.begin(); bit!=data.end(); ++bit){
        const Band& b = *bit;

        double emin(floor(b.emin()+0.5) ), emax(floor(b.emax()+0.5));
        if( emin < s_emin ) continue;
        if( emax > s_emax ) break;
        // 	std::cout << "XXX Pushing back energy band: " << emin << " " << emax << std::endl;
        bands.push_back(std::make_pair(&b,true));
    }
    for( std::list<std::pair<const Band*,bool> >::iterator bit1 = bands.begin(); bit1 !=bands.end(); ++bit1){
        if( ! bit1->second) continue; // already used

        // create new SimpleLikelihood object
        const Band& b1( *(*bit1).first );
        // limit umax if requested.
        double umax(SimpleLikelihood::defaultUmax()),
            roi(b1.sigma()*sqrt(2.*umax)),
            maxroi(maxROI()*M_PI/180), 
            minroi(minROI()*M_PI/180);
        if( maxroi>0 && roi>maxroi){
            umax = 0.5*sqr(maxroi/b1.sigma());
        }else if( minroi>0 && roi<minroi){
            umax = 0.5*sqr(minroi/b1.sigma());
        }
        BandBackground * back(0);
        if( m_background !=0){
            back= new BandBackground(*m_background, b1);
            m_backlist.push_back(back); // save to delete in dtor
        }
        SimpleLikelihood* sl = new SimpleLikelihood(b1, m_dir, umax, back);
        if( merge() ){
            // add other bands with identical properties if requested
            for( std::list<std::pair<const Band*,bool> >::iterator bit2(bit1); bit2 !=bands.end(); ++bit2){
                if( bit1==bit2) continue;
                const Band& b2( *(*bit2).first );
                if( b1.nside() == b2.nside() && b2.sigma() == b1.sigma() ){
                    if( m_background !=0) {
                        // add second background for the back events -- but do not include potential other point sources
                        const skymaps::SkySpectrum& diffuse (*(*m_background)[0].second);
                        back= new BandBackground( diffuse, b2); 
                        sl->addBand(b2, back); 
                        m_backlist.push_back(back); // save to delete in dtor
                    }
                    (*bit2).second=false; // mark as used
                }
            }
        }
        this->push_back( sl );
    }

    if( this->empty()){
        throw std::invalid_argument("PointSourceLikelihood::setup: no bands to fit!");
    }
}

PointSourceLikelihood::~PointSourceLikelihood()
{
    for( iterator it = begin(); it!=end(); ++it){
        delete *it;
    }
    delete m_background;
    for( std::vector<skymaps::BandBackground*>::iterator i(m_backlist.begin()); i!=m_backlist.end(); ++i){
        delete *i;
    }
}

double PointSourceLikelihood::TS()const
{ 
   double ret(0);
   for (Iterator it(begin(),end()); it!=end(); ++it){
       ret += (*it)->TS();
   }
   return ret;
}


double PointSourceLikelihood::maximize()
{
    m_TS = 0;
    Iterator it(begin(),end());
    for( ; it!=end() ; ++it){
        SimpleLikelihood& like = **it;
        std::pair<double,double> a(like.maximize());
        if( a.first > s_minalpha ) {
            m_TS+= like.TS();
        }
    }
    return m_TS;
}

void PointSourceLikelihood::setDir(const astro::SkyDir& dir, bool subset){
    for( iterator it = begin(); it!=end(); ++it){
        (*it)->setDir(dir,subset);
    }
    m_dir = dir;
}

const CLHEP::Hep3Vector& PointSourceLikelihood::gradient() const{
    m_gradient=CLHEP::Hep3Vector(0);  
    Iterator it(begin(),end());
    for( ; it!=end() ; ++it){
        double ts_i((*it)->TS());
        //if( verbose() ) std::cout << "TS: " << (*it)->TS() << std::endl;
        if( ts_i< s_TScut) continue; // do not count if TS small
        CLHEP::Hep3Vector grad((*it)->gradient());
        double curv((*it)->curvature());
        if( curv > 0 ) m_gradient+= grad;
    }
    return m_gradient;
}

double PointSourceLikelihood::curvature() const{
    double t(0);
    Iterator it(begin(),end());
    for( ; it!=end(); ++it){
        if( (*it)->TS()< s_TScut) continue;
#if 0 // Marshall?
        it->second->gradient();
#endif
        double curv((*it)->curvature());
        if( curv>0 )  t+= curv;
    }
    if( t==0){ t=1e-6;} // protect for no data!
    return t;
}

void PointSourceLikelihood::printSpectrum()
{

    using std::setw; using std::left; using std::setprecision; 
    bool extended(s_diffuse!=0 && SimpleLikelihood::extended_likelihood());
    out() << "\nSpectrum of source " << m_name << " at ra, dec=" 
        << setprecision(6) << m_dir.ra() << ", "<< m_dir.dec() 
        << std::endl;

    out() 
        << "                               ---shape analysis---- "
        << (extended? " ----------poisson----------   -------combined-----\n" : "\n")
        << "  emin eclass roi(deg) events  signal_fract(%)    TS "
        << (extended? "backgnd signal_fract(%)   TS   signal_fract(%)   TS  " : "")
        << std::right << std::endl;

    double simpleTS(0), extendedTS(0), poissonTS(0);
    bool save_extended( SimpleLikelihood::extended_likelihood());

    for( const_iterator it = begin(); it!=end(); ++it){

        SimpleLikelihood& levellike = **it;
        const skymaps::Band& band ( levellike.band() );

        double bkg(levellike.background());
        out()  << std::fixed << std::right 
            << setw(7) << static_cast<int>( band.emin()+0.5 )
            << setw(5) << (levellike.bands().size()>1? -1 : band.event_class())
            << setw(9) << setprecision(2)<< levellike.band().sigma()*sqrt(2.*levellike.umax())*180/M_PI 
            << setw(8) << levellike.photons()
            ;

        if( levellike.photons()==0) {
            out() << std::endl; 
            continue;
        }
        SimpleLikelihood::enable_extended_likelihood(false);
        std::pair<double,double> a(levellike.maximize());
        double ts(levellike.TS()); 
        if( a.first > s_minalpha ) {
            simpleTS+=ts;
        }

        out() << setprecision(1) 
            << setw(7)<< 100*a.first<<" +/- "
            << setw(4)<< 100*(std::min(0.999,a.second)) 
            << setw(7)<< setprecision(0)<< ts ;

        if(conf()) {
            ConfidenceLevel cl(**it,m_dir);
            out() << setprecision(2) << setw(4) << cl();
        }

        // output from background analysis if present
        if(extended) {
            // estimate from count analysis
            double apois(1- std::min(1.,bkg/levellike.photons()))
                , sigpois(1./sqrt(levellike.poissonDerivatives(apois).second));
            double ts(-2* (levellike.poissonLikelihood(apois)-levellike.poissonLikelihood(0)));
            out()  
                << setw(7) << setprecision(1) << bkg
                << setw(6)  << 100*(apois)<< " +/- "
                << setw(4)  << 100.*std::min(0.999,sigpois)
                << setw(7)  << setprecision(0)<< ts 
                ;
            poissonTS +=ts;

            // combinded estimate
            SimpleLikelihood::enable_extended_likelihood();
            std::pair<double,double> a(levellike.maximize());
            ts =(levellike.TS());
            extendedTS+=ts;

            out() << setprecision(1) 
                << setw(7)<< 100*a.first<<" +/- "
                << setw(4)<< 100*std::min(0.999,a.second )
                << setw(7)<< setprecision(0)<< ts ;

        }
        out() << std::endl;
    }
    SimpleLikelihood::enable_extended_likelihood(save_extended);
    out()   << setw(40) << "TS sum  " << std::right
        <<  setprecision(0) << setw(12) << simpleTS;
    if( extended ){
        out() << setw(29) << poissonTS << setw(23) << extendedTS;
    }
    out()<<setprecision(6)<< std::left<< std::endl;
}

std::vector<double> PointSourceLikelihood::energyList()const
{

    std::vector<double> energies;
    if( size()>0) {
        const_iterator it (begin());
        for( ; it!= end(); ++it){
            double emin((*it)->band().emin());
            if( energies.size()==0 || energies.back()!= emin){
                energies.push_back(emin);
            }
        }
        energies.push_back( back()->band().emax() );
    }
    return energies;

}
double PointSourceLikelihood::localize(int skip1, int skip2)
{
    double t(100);
    for( int skip=skip1; skip<=skip2; ++skip){
        double sigmax(maxSig());
        //instead of skipping bands, try to decrease PSF width requirement
        set_maxSig(sigmax/(sqrt(1.*(1<<skip))));
        t = localize();
        //reset the value to default in case of catastrophy
        set_maxSig(sigmax);
        if (t<1) break;
    }
    return t;
}

double PointSourceLikelihood::localize()
{
    using std::setw; using std::left; using std::setprecision; using std::right;
    using std::fixed;
    int wd(10), iter(0), maxiter(5);
    double steplimit(10.0), // in units of sigma
        stepmin(0.25);     // quit if step this small, in units of sigma
    double backoff_ratio(0.5); // scale step back if TS does not increase
    int backoff_count(2);

    if( verbose()){
        out() 
            << "      Searching for best position, maximum sigma allowed: "<< maxSig() <<" deg.\n"
            << setw(wd) << left<< "Gradient   " 
            << setw(wd) << left<< "delta  "   
            << setw(wd) << left<< "ra"
            << setw(wd) << left<< "dec "
            << setw(wd) << left<< "error "
            << setw(wd) << left<< "Ts "
            <<std::endl;
    }
    SkyDir last_dir(dir()); // save current direction
    setDir(dir(), true);    // initialize
    double oldTs( maximize()); // initial (partial) TS
    bool backingoff;  // keep track of backing


    for( ; iter<maxiter; ++iter){
        CLHEP::Hep3Vector grad( gradient() );
        double     curv( curvature() );

        // check that resolution is ok: if curvature gets small or negative we are lost
        if( curv < 1.e4){
            if( verbose()) out() << "  >>>aborting, lost" << std::endl;
            return 98.;
            break;
        }
        double     sig( 1/sqrt(curv))
            ,      gradmag( grad.mag() )
            ;
        //,      oldTs( TS() );
        CLHEP::Hep3Vector delta = grad/curv;
        double step(delta.mag());

        if( verbose() ){
            out() << fixed << setprecision(0)
                <<  setw(wd-2)  << right<< gradmag << "  "
                <<  setprecision(4)
                <<  setw(wd) << left<< step*180/M_PI
                <<  setw(wd) << left<< m_dir.ra()
                <<  setw(wd) << left<< m_dir.dec() 
                <<  setw(wd) << left<< sig*180/M_PI
                <<  setw(wd) << left <<setprecision(1)<< oldTs
                <<  right <<setprecision(3) <<std::endl;
        }
#if 0
        if( step*180/M_PI > s_maxstep) {
            if( verbose() ){ out() << " >>> aborting, attempted step " 
                << (step*180/M_PI) << " deg  greater than limit " 
                << s_maxstep << std::endl;
            }
            return 97.;
            break;
        }
#endif
        // check for too large step, limit to steplimt* sigma
        if( step > steplimit* sig ) {
            delta = steplimit*sig* delta.unit();
            if( verbose() ) out() << setw(52) << "reduced step to "
                <<setprecision(5)<< delta.mag() << std::endl;
        }

        // here decide to back off if likelihood does not increase
        CLHEP::Hep3Vector olddir(m_dir()); int count(backoff_count); 
        backingoff =true;
        while( count-->0){
            m_dir = olddir -delta;
#if 1
            setDir(m_dir,true);
            double newTs(maximize());
#else // make comparison without speedup
            oldTs=TSmap(m_dir); 
            double newTs(TSmap(m_dir));
            setDir(m_dir, true);
#endif
            if( newTs > oldTs-0.01 ){ // allow a little slop
                oldTs=newTs;
                backingoff=false;
                break;
            }
            delta*=backoff_ratio; 
            if( verbose() ){ out()<< setw(56) <<setprecision(1) << newTs << " --back off "
                <<setprecision(5)<< delta.mag() << std::endl; }

        }

        if( gradmag < 0.1 || delta.mag()< stepmin*sig) break;
    }// iter loop
    if( iter==maxiter ){ //&& ! backingoff ){
        if( verbose() ) out() << "   >>>did not converge" << std::endl;
        setDir(last_dir()); // restore position
        return 99.;
    }
    if(verbose() ){
        out() << "    *** good fit *** " <<dir().ra()<< "  " << dir().dec()<< std::endl;
    }
    double errcirc=errorCircle();
    //least squares fit to surface
    if(fitlsq()) {
        LeastSquaresFitter lsq(*(this));
        errcirc=lsq.err();
    }
    return errcirc;
}



double PointSourceLikelihood::logLikelihood(const skymaps::SpectralFunction& model, bool extended)const
{
    double result(0);
    const_iterator it = begin();
    for( ; it!=end(); ++it){
        const SimpleLikelihood& sl( **it);
        // expected is the product of total from model times fraction in aperature
        double expected( model.expected(dir(), sl.band())  * sl.aperature_correction() );
        result += extended? sl.extendedLikelihood(expected) 
            : sl.logLikelihood(expected);
    }
    return result;
}

double PointSourceLikelihood::value(const astro::SkyDir& dir, double energy) const
{
    double result(0);
    const_iterator it = begin();
    for( ; it!=end(); ++it){
        const Band& band ( (*it)->band() );
        if( energy >= band.emin() && energy < band.emax() ){
            result += (**it)(dir);
        }
    }
    return result;

}

double PointSourceLikelihood::band_value(const astro::SkyDir& dir, const skymaps::Band& band)const
{
    double result(0);
    const_iterator it = begin();
    for( ; it!=end(); ++it){
        const Band& lband ( (*it)->band() );
        if( lband.event_class()==band.event_class() && lband.emin()==band.emin() ){
            return (**it)(dir);
        }
    }
    throw std::runtime_error("PointSourceLikelihood::band_value: band not found");
    return result;
}


double PointSourceLikelihood::display(const astro::SkyDir& dir, double energy, int mode) const
{
    const_iterator it = begin();
    for( ; it!=end(); ++it){
        const Band& band ((*it)->band());
        if( energy >= band.emin() && energy < band.emax() )break;
    }
    if( it==end() ){
        throw std::invalid_argument("PointSourceLikelihood::display--no fit for the requested energy");
    }
    return (*it)->display(dir, mode);
}


///@brief integral for the energy limits, in the given direction
double PointSourceLikelihood::integral(const astro::SkyDir& dir, double emin, double emax)const
{
    // implement by just finding the right bin
    return value(dir, sqrt(emin*emax) );
}

//-------------------------------------------------------------------------------------------
//            Background management
//-------------------------------------------------------------------------------------------
const skymaps::SkySpectrum* PointSourceLikelihood::set_diffuse(const skymaps::SkySpectrum* diffuse, double exposure)
{  
    // save current to return
    const skymaps::SkySpectrum* ret =   s_diffuse;

    s_diffuse = diffuse==0? 0 : new Background(*diffuse, exposure);

    return ret;
}

const skymaps::SkySpectrum* PointSourceLikelihood::set_diffuse(const skymaps::SkySpectrum* diffuse, 
                                                               std::vector<const skymaps::SkySpectrum*> exposures)
{  
    // save current to return
    const skymaps::SkySpectrum* ret =   s_diffuse;

    s_diffuse = new Background(*diffuse, exposures);

    return ret;
}

const skymaps::Background* PointSourceLikelihood::set_background(const skymaps::Background* background)
{
    const skymaps::Background* back = s_diffuse;
    s_diffuse = background;
    return back;
}
const skymaps::Background* PointSourceLikelihood::clear_background(){
    return PointSourceLikelihood::set_background(0);
}; 


void PointSourceLikelihood::addBackgroundPointSource(const PointSourceLikelihood* fit)
{
    if( fit==this){
        throw std::invalid_argument("PointSourceLikelihood::setBackgroundFit: cannot add self as background");
    }
    if( m_background==0){
        throw std::invalid_argument("PointSourceLikelihood::setBackgroundFit: no diffuse background");
    }

    if( s_verbose>0 ) {
        out() << "Adding source " << fit->name() << " to background" << std::endl;
    }
    m_background->add(fit);
    setDir(dir()); // recomputes background for each SimpleLikelihood object
}

void PointSourceLikelihood::clearBackgroundPointSource()
{
    if( m_background==0){
        throw std::invalid_argument("PointSourceLikelihood::setBackgroundFit: no diffuse to add to");
    }
    while( m_background->size()>1) {
        m_background->pop_back();
    }
    setDir(dir()); // recomputes background for each SimpleLikelihood object
}

const skymaps::SkySpectrum * PointSourceLikelihood::background()const
{
    return m_background;
}
//-------------------------------------------------------------------------------------------


/// @brief set radius for individual fits
void PointSourceLikelihood::setDefaultUmax(double umax)
{ 
    SimpleLikelihood::setDefaultUmax(umax); 
}
double PointSourceLikelihood::set_tolerance(double tol)
{
    double old(SimpleLikelihood::tolerance());
    SimpleLikelihood::setTolerance(tol);
    return old;
}

double PointSourceLikelihood::TSmap(const astro::SkyDir&sdir, int band)const
{
    if( band>-1) {
        return this->at(band)->TSmap(sdir);
    }
    double ret(0);
#if 1
    Iterator it(begin(),end()); // define by skipping bands with sigma> sigMax
#else
    const_iterator it = begin();
#endif
    for( ; it!=end(); ++it){
        ret += (*it)->TSmap(sdir);
    }
    return ret;
}

//=======================================================================
//         PSLdisplay implementation
PSLdisplay::PSLdisplay(const PointSourceLikelihood & psl, int mode)
: m_psl(psl)
, m_mode(mode)
{}

double PSLdisplay::value(const astro::SkyDir& dir, double e)const{
    return m_psl.display(dir, e, m_mode);
}

///@brief integral for the energy limits, in the given direction -- not impleme
double PSLdisplay::integral(const astro::SkyDir& dir, double a, double b)const{
    return value(dir, sqrt(a*b));
}

std::string PSLdisplay::name()const
{
    static std::string type[]={"density", "data", "background", "fit", "residual", "TS"};
    if( m_mode<0 || m_mode>5) return "illegal";
    return m_psl.name()+"--"+type[m_mode];

}
//=======================================================================
//        TSmap implementation

TSmap::TSmap(const PointSourceLikelihood& psl, int band)
: m_data(0)
, m_psl(&psl)
, m_band(band)
, m_offset(psl.TSmap(psl.dir()))
{}

TSmap::TSmap(const skymaps::BinnedPhotonData& data, int band)
: m_data(&data)
, m_psl(0)
, m_band(band)
, m_offset(0)
{}

void TSmap::setPointSource(const PointSourceLikelihood& psl){
    m_psl = &psl;
}


double TSmap::operator()(const astro::SkyDir& sdir)const
{
    if( m_data!=0 ){
        PointSourceLikelihood psl(*m_data, "temp", sdir);
        if( m_psl!=0){
            psl.addBackgroundPointSource(m_psl);
        }
        psl.maximize();
        if( m_band>-1) return psl.at(m_band)->TS();
        return psl.TS();

    }
    // using current fit.
    return m_psl->TSmap(sdir, m_band)- (m_band==-1?m_offset:0);
}
