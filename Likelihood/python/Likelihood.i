// -*- mode: c++ -*-
%module Likelihood
%{
#include "irfLoader/Loader.h"
#include "irfInterface/IrfsFactory.h"
#include "optimizers/Lbfgs.h"
#include "optimizers/Drmngb.h"
#include "optimizers/Minuit.h"
#include "optimizers/Optimizer.h"
#include "optimizers/Parameter.h"
#include "optimizers/ParameterNotFound.h"
#include "optimizers/Function.h"
#include "optimizers/FunctionFactory.h"
#include "Likelihood/ResponseFunctions.h"
#include "Likelihood/Source.h"
#include "Likelihood/DiffuseSource.h"
#include "Likelihood/EventArg.h"
#include "Likelihood/Event.h"
#include "Likelihood/ExposureMap.h"
#include "Likelihood/FitsImage.h"
#include "Likelihood/logSrcModel.h"
#include "Likelihood/Npred.h"
#include "Likelihood/OneSourceFunc.h"
#include "Likelihood/OptEM.h"
#include "Likelihood/PointSource.h"
#include "Likelihood/RoiCuts.h"
#include "Likelihood/ScData.h"
#include "Likelihood/SkyDirArg.h"
#include "Likelihood/SkyDirFunction.h"
#include "Likelihood/SourceFactory.h"
#include "Likelihood/SourceModel.h"
#include "Likelihood/SpatialMap.h"
#include "Likelihood/SrcArg.h"
#include "Likelihood/TrapQuad.h"
#include "Likelihood/Exception.h"
#include "Likelihood/LogLike.h"
#include "Likelihood/BinnedLikelihood.h"
#include <vector>
#include <string>
#include <exception>
using optimizers::Parameter;
using optimizers::ParameterNotFound;
using optimizers::Function;
using optimizers::Exception;
%}
%include stl.i
%include ../../../optimizers/v1r4/optimizers/Function.h
%include ../../../optimizers/v1r4/optimizers/FunctionFactory.h
%include ../../../optimizers/v1r4/optimizers/Optimizer.h
%include ../Likelihood/Exception.h
%include ../Likelihood/ResponseFunctions.h
%include ../Likelihood/Event.h
%include ../Likelihood/Source.h
%include ../Likelihood/SourceModel.h
%include ../Likelihood/DiffuseSource.h
%include ../Likelihood/EventArg.h
%include ../Likelihood/ExposureMap.h
%include ../Likelihood/FitsImage.h
%include ../Likelihood/LogLike.h
%include ../Likelihood/BinnedLikelihood.h
%include ../Likelihood/logSrcModel.h
%include ../Likelihood/Npred.h
%include ../Likelihood/OneSourceFunc.h
%include ../Likelihood/OptEM.h
%include ../Likelihood/PointSource.h
%include ../Likelihood/RoiCuts.h
%include ../Likelihood/ScData.h
%include ../Likelihood/SkyDirArg.h
%include ../Likelihood/SkyDirFunction.h
%include ../Likelihood/SourceFactory.h
%include ../Likelihood/SpatialMap.h
%include ../Likelihood/SrcArg.h
%include ../Likelihood/TrapQuad.h
%template(DoubleVector) std::vector<double>;
%template(DoubleVectorVector) std::vector< std::vector<double> >;
%template(StringVector) std::vector<std::string>;
%extend Likelihood::SourceFactory {
   optimizers::FunctionFactory * funcFactory() {
      optimizers::FunctionFactory * myFuncFactory 
         = new optimizers::FunctionFactory;
      myFuncFactory->addFunc("SkyDirFunction", 
                             new Likelihood::SkyDirFunction(), false);
      myFuncFactory->addFunc("SpatialMap", new Likelihood::SpatialMap(), 
                             false);
      return myFuncFactory;
   }
}
%extend Likelihood::LogLike {
   void print_source_params() {
      std::vector<std::string> srcNames;
      self->getSrcNames(srcNames);
      std::vector<Parameter> parameters;
      for (unsigned int i = 0; i < srcNames.size(); i++) {
         Likelihood::Source *src = self->getSource(srcNames[i]);
         Likelihood::Source::FuncMap srcFuncs = src->getSrcFuncs();
         srcFuncs["Spectrum"]->getParams(parameters);
         std::cout << "\n" << srcNames[i] << ":\n";
         for (unsigned int i = 0; i < parameters.size(); i++)
            std::cout << parameters[i].getName() << ": "
                      << parameters[i].getValue() << std::endl;
         std::cout << "Npred: "
                   << src->Npred() << std::endl;
      }
   }
   void src_param_table() {
      std::vector<std::string> srcNames;
      self->getSrcNames(srcNames);
      std::vector<Parameter> parameters;
      for (unsigned int i = 0; i < srcNames.size(); i++) {
         Likelihood::Source *src = self->getSource(srcNames[i]);
         Likelihood::Source::FuncMap srcFuncs = src->getSrcFuncs();
         srcFuncs["Spectrum"]->getParams(parameters);
         for (unsigned int i = 0; i < parameters.size(); i++)
            std::cout << parameters[i].getValue() << "  ";
         std::cout << src->Npred() << "  ";
         std::cout << srcNames[i] << std::endl;
      }
   }
   int getNumFreeParams() {
      return self->getNumFreeParams();
   }
   void getFreeParamValues(std::vector<double> & params) {
      self->getFreeParamValues(params);
   }
   optimizers::Optimizer * Minuit() {
      return new optimizers::Minuit(*self);
   }
   optimizers::Optimizer * Lbfgs() {
      return new optimizers::Lbfgs(*self);
   }
   optimizers::Optimizer * Drmngb() {
      return new optimizers::Drmngb(*self);
   }
   static void loadResponseFunctions(const std::string & respFuncs) {
      irfLoader::Loader::go();
      irfInterface::IrfsFactory * myFactory 
         = irfInterface::IrfsFactory::instance();
      
      typedef std::map< std::string, std::vector<std::string> > respMap;
      const respMap & responseIds = irfLoader::Loader::respIds();
      respMap::const_iterator it;
      if ( (it = responseIds.find(respFuncs)) != responseIds.end() ) {
         const std::vector<std::string> & resps = it->second;
         for (unsigned int i = 0; i < resps.size(); i++) {
            Likelihood::ResponseFunctions::
               addRespPtr(i, myFactory->create(resps[i]));
         }
      } else {
         throw std::invalid_argument("Invalid response function choice: "
                                     + respFuncs);
      }
   }
}
%extend Likelihood::BinnedLikelihood {
   void print_source_params() {
      std::vector<std::string> srcNames;
      self->getSrcNames(srcNames);
      std::vector<Parameter> parameters;
      for (unsigned int i = 0; i < srcNames.size(); i++) {
         Likelihood::Source *src = self->getSource(srcNames[i]);
         Likelihood::Source::FuncMap srcFuncs = src->getSrcFuncs();
         srcFuncs["Spectrum"]->getParams(parameters);
         std::cout << "\n" << srcNames[i] << ":\n";
         for (unsigned int i = 0; i < parameters.size(); i++)
            std::cout << parameters[i].getName() << ": "
                      << parameters[i].getValue() << std::endl;
      }
   }
   static Likelihood::
      BinnedLikelihood * create(const std::string & countsMapFile) {
      Likelihood::CountsMap * dataMap = 
         new Likelihood::CountsMap(countsMapFile);
      Likelihood::BinnedLikelihood * logLike = 
         new Likelihood::BinnedLikelihood(*dataMap, countsMapFile);
      return logLike;
   }
   int getNumFreeParams() {
      return self->getNumFreeParams();
   }
   void getFreeParamValues(std::vector<double> & params) {
      self->getFreeParamValues(params);
   }
   optimizers::Optimizer * Minuit() {
      return new optimizers::Minuit(*self);
   }
   optimizers::Optimizer * Lbfgs() {
      return new optimizers::Lbfgs(*self);
   }
   optimizers::Optimizer * Drmngb() {
      return new optimizers::Drmngb(*self);
   }
}
%extend Likelihood::Event {
   double ra() {
      return self->getDir().ra();
   }
   double dec() {
      return self->getDir().dec();
   }
   double scRa() {
      return self->getScDir().ra();
   }
   double scDec() {
      return self->getScDir().dec();
   }
}
