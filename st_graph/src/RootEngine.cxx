/** \file RootEngine.cxx
    \brief Implementation of class which encapsulates the Root graphics implementation.
    \author James Peachey, HEASARC/GSSC
*/
#include <cctype>
#include <cstdlib>
#include <csignal>
#include <stdexcept>
#include <vector>

#ifdef WIN32
typedef void (*sighandler_t) (int);
#endif

#include "TApplication.h"
#include "TGButton.h"
#include "TGClient.h"
#include "TGWindow.h"
#include "TStyle.h"
#include "TSystem.h"

#include "st_graph/IEventReceiver.h"
#include "st_graph/IFrame.h"

#include "RootEngine.h"
#include "RootFrame.h"
#include "RootPlot.h"
#include "RootPlotFrame.h"
#include "STGMainFrame.h"

namespace st_graph {

  RootEngine::RootEngine(): m_init_succeeded(false) {
    gSystem->ResetSignal(kSigBus);
    gSystem->ResetSignal(kSigSegmentationViolation);
    gSystem->ResetSignal(kSigSystem);
    gSystem->ResetSignal(kSigPipe);
    gSystem->ResetSignal(kSigIllegalInstruction);
    gSystem->ResetSignal(kSigQuit);
    gSystem->ResetSignal(kSigInterrupt);
    gSystem->ResetSignal(kSigWindowChanged);
    gSystem->ResetSignal(kSigAlarm);
    gSystem->ResetSignal(kSigChild);
    gSystem->ResetSignal(kSigUrgent);
    gSystem->ResetSignal(kSigFloatingException);
    gSystem->ResetSignal(kSigTermination);
    gSystem->ResetSignal(kSigUser1);
    gSystem->ResetSignal(kSigUser2);

    // If no TApplication already exists, create one.
    if (0 == gApplication) {
      // Ignore signals when creating the application.
      std::vector<sighandler_t> handlers(16);
      for (int ii = 0; ii < 16; ++ii) {
        handlers[ii] = signal(ii, SIG_IGN);
      }

      // Create application.
      int argc = 0;
      gApplication = new TApplication("st_graph", &argc, 0);

      // Restore signal handlers.
      for (int ii = 0; ii < 16; ++ii) {
        signal(ii, handlers[ii]);
      }
    }

    // Now test for success: if virtual X was set up
    // correctly, gClient will be non-0.
    if (0 == gClient)
      throw std::runtime_error("RootEngine::RootEngine could not initialize graphical environment");

    // Turn off "stats box".
    if (0 != gStyle) gStyle->SetOptStat("");

    m_init_succeeded = true;
  }

  void RootEngine::run() {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::run: graphical environment not initialized");

    // Display all frames currently linked to the top-level frame.
    RootFrame::ancestor()->display();

    // Run the Root event loop to handle the graphical displays.
    gApplication->Run(kTRUE);
  }

  void RootEngine::stop() {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::stop: graphical environment not initialized");

    RootFrame::ancestor()->unDisplay();
    gApplication->Terminate(0);
  }

  IFrame * RootEngine::createMainFrame(IEventReceiver * receiver, unsigned int width, unsigned int height) {
    // Receiver which terminates the application -- sensible default behavior for a main frame.
    class DefaultReceiver : public IEventReceiver {
      public:
        DefaultReceiver(Engine & engine): m_engine(engine) {}
        virtual void closeWindow(IFrame *) {
          m_engine.stop();
        }

      private:
        Engine & m_engine;
    };

    static DefaultReceiver s_default_receiver(*this);

    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createMainFrame: graphical environment not initialized");

    // If client did not supply a receiver, use the default one.
    if (0 == receiver) receiver = &s_default_receiver;

    // Create the Root widget.
    STGMainFrame * tg_widget = new STGMainFrame(this, width, height);

    // Give window manager a hint about where to display it.
    tg_widget->SetWMPosition(100, 50);

    // Create the IFrame which refers to it.
    RootFrame * frame = new RootFrame(receiver, tg_widget);

    // Connect appropriate Root Qt signals to this object's slot.
    tg_widget->Connect("CloseWindow()", "st_graph::RootFrame", frame, "closeWindow()");

    return frame;
  }

  IPlot * RootEngine::createPlot(const std::string & title, unsigned int width, unsigned int height, const std::string & style,
    const ISequence & x, const ISequence & y) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createPlot: graphical environment not initialized");

    // Create parent main frame.
    IFrame * mf = createMainFrame(0, width, height);

    // Create frame to hold plot. This frame owns and will delete its parent.
    IFrame * pf = new RootPlotFrame(mf, title, width, height, true);

    // Create plot. This plot owns and will delete its parent.
    return new RootPlot(pf, style, x, y, true);
  }

  IPlot * RootEngine::createPlot(const std::string & title, unsigned int width, unsigned int height, const std::string & style,
    const ISequence & x, const ISequence & y, const std::vector<std::vector<double> > & z) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createPlot: graphical environment not initialized");

    // Create parent main frame.
    IFrame * mf = createMainFrame(0, width, height);

    // Create frame to hold plot. This frame owns and will delete its parent.
    IFrame * pf = new RootPlotFrame(mf, title, width, height, true);

    // Create plot. This plot owns and will delete its parent.
    return new RootPlot(pf, style, x, y, z, true);
  }

  IPlot * RootEngine::createPlot(IFrame * parent, const std::string & style, const ISequence & x, const ISequence & y) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createPlot: graphical environment not initialized");

    return new RootPlot(parent, style, x, y);
  }

  IPlot * RootEngine::createPlot(IFrame * parent, const std::string & style, const ISequence & x, const ISequence & y,
    const std::vector<std::vector<double> > & z) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createPlot: graphical environment not initialized");

    return new RootPlot(parent, style, x, y, z);
  }

  IFrame * RootEngine::createPlotFrame(IFrame * parent, const std::string & title, unsigned int width, unsigned int height) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createPlotFrame: graphical environment not initialized");

    return new RootPlotFrame(parent, title, width, height);
  }

  IFrame * RootEngine::createButton(IFrame * parent, IEventReceiver * receiver, const std::string & style,
    const std::string & label) {
    if (!m_init_succeeded) throw std::runtime_error("RootEngine::createButton: graphical environment not initialized");

    // Need the Root frame of the parent object.
    RootFrame * rf = dynamic_cast<RootFrame *>(parent);
    if (0 == rf) throw std::logic_error("RootEngine::createButton was passed an invalid parent frame pointer");

    // Make style check case insensitive.
    std::string lc_style = style;
    for (std::string::iterator itor = lc_style.begin(); itor != lc_style.end(); ++itor) *itor = tolower(*itor);

    TGButton * tg_widget = 0;
    if (std::string::npos != lc_style.find("text")) {
      // Create the Root widget.
      tg_widget = new TGTextButton(rf->getTGFrame(), label.c_str());
    } else { 
      throw std::logic_error("RootEngine::createButton cannot create a button with style " + style);
    }

    // Create the IFrame which refers to it.
    IFrame * frame = new RootFrame(parent, receiver, tg_widget);

    // Connect appropriate Root Qt signals to this object's slot.
    tg_widget->Connect("Clicked()", "st_graph::RootFrame", frame, "clicked()");

    return frame;
  }

}
