#ifndef ResultsFile_h
#define ResultsFile_h

#include "pointlike/SourceLikelihood.h"
#include "pointlike/Data.h"
#include "pointlike/SpectralFitter.h"
#include "tip/IFileSvc.h"
#include "tip/Table.h"

namespace pointlike {
  class ResultsFile {
  private:
    tip::Table* srcTab;
    tip::IFileSvc& fileSvc;
    tip::Table::Iterator srcTabItor;  
    std::vector<double> emin;
    std::vector<double> emax;
    int levels;
    double eratio;

    bool fields_created;
    
  public:

    ResultsFile (const std::string& filename,const Data& datafile, int nsources);
    ~ResultsFile(){writeAndClose();};
       
    void fill(SourceLikelihood& like);
    void fill(SourceLikelihood& like,SpectralFitter& fitter);
    
    void writeAndClose();
  };
};

#endif
