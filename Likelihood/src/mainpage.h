// Mainpage for doxygen

/** @mainpage package Likelihood

 @authors James Chiang, Toby Burnett, Pat Nolan, Karl Young, and others

 @section intro Introduction

 This package implements an extended maximum likelihood (EML)
 calculation for analyzing LAT event data.

 These data are generally assumed to be in a format consistent with
 that produced by the Level 1 Event Data Extractor, otherwise known as
 U1.  The data may alternatively have been generated by the
 observation simulator (O2).  Accordingly, use of this tool for
 analysis of Event data requires access to a complete set of
 accompanying spacecraft orbit and attitude information, obtained
 using the Pointing, Livetime History Extractor (U3) or the orbit
 simulator tool (O1), as well as access to appropriate instrument
 response function data (i.e., CALDB).

 However, the classes and methods used here are intended to be
 sufficiently general so that any properly implemented Statistic
 subclass should be able to be analyzed with this package, whether the
 Statistic is LAT-specific or not.

 @section LatStatModel The Unbinned log-Likelihood

 For LAT event analysis, the default statistical model we assume is
 the unbinned log-likelihood:

 \f[
 \log L = \sum_j \left[\log \left(\sum_i M_i(x_j; \vec{\alpha_i})\right)\right] 
        - \sum_i \left[\int dx M_i(x; \vec{\alpha_i})\right]
 \f]

 Here \f$x_j\f$ is the \f$j\f$th photon Event, as specified by
 apparent energy, direction, and arrival time. The function \f$M_i(x;
 \vec{\alpha_i})\f$ returns the flux density in units of counts per
 energy-time-area-solid angle (i.e., photon fluxes convolved through
 the instrument response) for the \f$i\f$th Source at a point \f$x\f$
 in the Event configuration space, hereafter known as the "data
 space".  Each \f$M_i\f$ is defined, in part, by a vector of parameter
 values \f$\vec{\alpha_i}\f$; collectively, the \f$\vec{\alpha_i}\f$
 vectors form the space over which the Statistic (also known as the
 objective function) is to be optimized.  The integral over the data
 space in the second term is the predicted number of Events expected
 to be seen from Source \f$i\f$.

 @section classes Important Classes

 Cast in this form, the problem lends itself to being described by the
 following classes and their descendants:

   - Likelihood::Function This class acts as a "functor" object in
   that the function call operator () is overloaded so that Function
   objects behave like ordinary C functions.  Several methods are also
   provided for accessing the model Parameters and derivatives with
   respect to those Parameters, either singly or in groups.  The
   behavior of this class is greatly facilitated by the Parameter and
   Arg classes.

   - Likelihood::Parameter This is essentially an NTuple containing
   model parameter information (and access methods) comprising the
   parameter value, scale factor, name, upper and lower bounds and
   whether the parameter is to be considered free or fixed in the
   fitting process.

   - Likelihood::Arg This class wraps arguments to Function objects
   so that Function's derivative passing mechanisms can be inherited
   by subclasses regardless of the actual type of the underlying
   argument.  For example, in the log-likelihood, we define
   Likelihood::logSrcModel, a Function subclass that returns the
   quantity inside the square brackets of the first term on the rhs.
   Acting as a function, logSrcModel naturally wants to take an Event
   as its argument, so we wrap an Event object with EventArg.
   Similarly, the quantity in the square brackets of the second term
   on the rhs we implement as the Likelihood::Npred class.  This class
   wants to have a Source object as its argument, which we wrap with
   the SrcArg class.

   - Likelihood::Statistic Subclasses of this are the objective
   functions to be optimized in order to estimate model parameters.
   Although these are in the Function hierarchy, their functor-like
   behavior differs in that _unwrapped_ (i.e., not Arg) vectors of the
   Parameters themselves are passed via the function call operator,
   ().  (This violates the "isa" convention for subclasses, so some
   refactoring is probably warranted.)

   - Likelihood::Source An abstract base class for gamma-ray sources.
   It specifies four key methods (as pure virtual functions); the
   latter two methods are wrapped by the Npred class in order to give
   them Function behavior:
      - fluxDensity(...): counts per energy-time-area-solid angle
      - fluxDensityDeriv(...): derivative wrt a Parameter
      - Npred(): predicted number of photons in the ROI
      - NpredDeriv(...): derivative of Npred wrt a Parameter

   - Likelihood::Event An NTuple containing photon event arrival
   time, apparent energy and direction, as well as spacecraft attitude
   information at the event arrival time and event-specific response
   function data for use with components of the diffuse emission
   model.

   - Likelihood::Response This hierarchy provides interfaces to the
   instrument response functions, the point-spread function (Psf), the
   effective area (Aeff), and the energy dispersion (not yet
   implemented).  These subclasses are all Singleton.

   - Likelihood::RoiCuts An NTuple Singleton class that contains the
   "region-of-interest" cuts.  These are essentially the bounds of the
   data space as a function of arrival time, apparent energy, apparent
   direction, zenith angle, etc..  Note that these bounds need not
   enclose a simply connected region.

   - Likelihood::ScData A Singleton object that contains the
   spacecraft data NTuples (ScNtuple).

   - Likelihood::SpectrumFactory This class implements the Prototype
   pattern in order to provide a common point of access for retrieving
   and storing Functions for spectral modeling.  Basic Functions such
   as Likelihood::PowerLaw, Likelihood::Gaussian, and
   Likelihood::AbsEdge are provided by default.  Clients can combine
   models using the Likelihood::CompositeFunction hierarchy, store
   those models in SpectrumFactory, and later, clone those stored
   models for use in other contexts.

   - Likelihood::SourceFactory This class provides a common access
   point for retrieving and storing Sources.  A
   Likelihood::PointSource, modeled with a PowerLaw, is provided by
   default.  Sources that have been constructed to comprise position
   and spectral information can be stored here, then cloned for later
   use.

 <hr>
 @section notes release.notes
 release.notes

 <hr>
 @section requirements requirements
 @verbinclude requirements

 <hr> 
 @todo DiffuseSource class
 @todo Error estimates, confidence regions, etc. 
 @todo SWIG or Boost.Python
 @todo Energy dispersion
 @todo Generalize Npred calculation, e.g., zenith angle cuts, fit-able 
       source locations
 @todo CCfits
 @todo Minuit++
 
 */
