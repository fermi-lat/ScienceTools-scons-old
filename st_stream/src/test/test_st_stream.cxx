/** \file st_stream_test.cxx
    \brief Test program for st_stream library.
    \author James Peachey, HEASARC/GSSC
*/
#include <fstream>
#include <iostream>
#include <string>

#include "st_stream/Stream.h"
#include "st_stream/StreamFormatter.h"
#include "st_stream/st_stream.h"

using namespace st_stream;

// Single global formatter for sample1.
StreamFormatter & formatter1() {
  // This cannot simply be instantiated at global scope because the maximum chatter, name of executable, etc.
  // are initialized after execution commences.
  static StreamFormatter s_format("", "", 3);
  return s_format;
}

void sample1() {
  // Optional: set name of current function.
  formatter1().setMethod("sample1()");

  formatter1().info() << "Wrote to formatter1().info() (with implicit default chatter of 3)" << std::endl;
  formatter1().info(1) << "Wrote to formatter1().info(1)" << std::endl;
  formatter1().info(4) << "Wrote to formatter1().info(4). This should not be displayed because the chatter is " <<
    "higher than the global maximum chatter level." << std::endl;
}

void sample2() {
  // A formatter specific to this function.
  StreamFormatter formatter2("", "sample2()", 4);
  formatter2.warn() << "Wrote to formatter2.warn(). This should not be displayed because formatter2's " <<
    "default chatter is higher than the global maximum chatter level." << std::endl;
  formatter2.warn(3) << "Wrote to formatter2.warn(3). This should appear. " <<
    "Note that the prefix repeats at the" << std::endl << "beginning of each new line." << std::endl;
}

void sample3() {
  // A formatter used throughout a class instance.
  class MyClass {
    public:
      MyClass(): m_formatter3("MyClass", "", 3) {}

      void myDebug() {
        m_formatter3.setMethod("myDebug");
        m_formatter3.debug() << "Wrote to m_formatter3.debug(). If debugging were disabled, this would not appear." << std::endl;

        // Explicitly enable debugging for this object. Useful, but only during development.
        m_formatter3.setDebugMode();
        m_formatter3.debug() << "Wrote to m_formatter3.debug(). This would appear even if debugging were initially disabled." <<
          std::endl;

        // Explicitly disable debugging for this object. Useful, but only during development.
        m_formatter3.setDebugMode(false);
        m_formatter3.debug() << "Wrote to m_formatter3.debug(). This should not appear because debugging was locally disabled." <<
          std::endl;
        m_formatter3.debug() << "This would not affect the debug setting of any other objects." << std::endl;
      }

      void myErr() {
        m_formatter3.setMethod("myErr");
        m_formatter3.err() << "Wrote to m_formatter3.err()" << std::endl;
      }

      void myInfo() {
        m_formatter3.setMethod("myInfo");
        m_formatter3.info() << "Wrote to m_formatter3.info()" << std::endl;
      }

      void myOut() {
        m_formatter3.setMethod("myOut");
        m_formatter3.out() << "Wrote to m_formatter3.out()" << std::endl;
      }

      void myWarn() {
        m_formatter3.setMethod("myWarn");
        m_formatter3.warn() << "Wrote to m_formatter3.warn()" << std::endl;
      }

    private:
      StreamFormatter m_formatter3;
  };

  MyClass object;
  object.myDebug();
  object.myErr();
  object.myInfo();
  object.myOut();
  object.myWarn();
}

int main() {
  // Before initializing standard streams, write to stout. This should have no effect.
  stout << "This was written before initializing standard streams, so it should not appear anywhere!" << std::endl;

  // Set max_chat used for tests.
  unsigned int max_chat = 3;

  // Initialize standard streams with maximum chatter of max_chat.
  InitStdStreams("test_st_stream", max_chat, true);

  // Run sample codes first.
  sample1();
  sample2();
  sample3();

  // Initialize standard streams again with max_chat == 0 -- should have no effect.
  InitStdStreams("wrong_executable", 0, false);

  std::cout << "After this, there should be exactly one line on each of sterr, stlog and stout." << std::endl;

  // Test direct writes to standard streams.
  sterr << "This should appear on std::cerr." << std::endl;
  stlog << "This should appear on std::clog." << std::endl;
  stout << "This should appear on std::cout." << std::endl;

  // Create a file-based STL stream.
  std::string out_file = "test_st_stream-out";
  std::ofstream std_os(out_file.c_str());

  // Verify that the file was opened correctly.
  if (std_os.bad()) {
    std::cerr << "ERROR: could not open output file " << out_file << std::endl;
    return 1;
  }

  // Connect all standard streams to the output file.
  sterr.connect(std_os);
  stlog.connect(std_os);
  stout.connect(std_os);

  // Also disconnect them from standard streams to prevent any further notices.
  sterr.disconnect(std::cerr);
  stlog.disconnect(std::clog);
  stout.disconnect(std::cout);

  // Write something directly to each stream.
  std_os << "Three lines should now be written to this file with no prefix, one via each stream:" << std::endl;
  sterr << Chat(max_chat + 1) << "Despite Chat(" << max_chat + 1 << ") this was written to sterr." << std::endl;
  stlog << Chat(max_chat + 1) << "Despite Chat(" << max_chat + 1 << ") this was written to stlog." << std::endl;
  stout << Chat(max_chat + 1) << "Despite Chat(" << max_chat + 1 << ") this was written to stout." << std::endl;

  // Create a stream which forwards to stout, but has a maximum chatter, which can be used to suppress some output.
  OStream my_out(max_chat);
  my_out.connect(stout);

  // Test that this works correctly with different chat levels.
  std_os << "Three lines should now be written to this file via my_out:" << std::endl;
  my_out << "This was written to my_out with default chat level." << std::endl;
  my_out << Chat(max_chat - 1) << "This was written to my_out with maximum chatter set to " << max_chat - 1 << std::endl;
  my_out << Chat(max_chat) << "This was written to my_out with maximum chatter set to " << max_chat << std::endl;
  my_out << Chat(max_chat + 1) <<
    "THIS SHOULD NOT APPEAR! This was written to my_out with maximum chatter set to " << max_chat + 1 << std::endl;
  my_out << "THIS SHOULD NOT APPEAR! This was written to my_out after maximum chatter was set to " << max_chat + 1 << std::endl;

  // Add the method name to the output stream's prefix.
  my_out.setPrefix("exec_name: ");

  // Make certain the prefix appears.
  std_os << "The next line should begin with a prefix of \"exec_name: \"" << std::endl;

  // Write line with prefix.
  my_out << Chat(max_chat) <<
    "This was written to my_out with explicit Chat(" << max_chat << ") after prefix was set." << std::endl;

  // Create a formatter with a default chatter level which should not be displayed.
  StreamFormatter sf1("", "", max_chat + 1);
  std_os << "A line with a prefix of \"test_st_stream: WARNING: \" should follow this line." << std::endl;
  sf1.warn() << "THIS SHOULD NOT APPEAR! This was written to sf1.warn()" << std::endl;
  sf1.warn(0) << "This was written to sf1.warn(0), and should always appear." << std::endl;
  sf1.warn() << "THIS SHOULD NOT APPEAR! This was written to sf1.warn(" << max_chat + 1 << ")." << std::endl;

  // Now include a method name in the warning.
  std_os << "A line with a prefix of \"test_st_stream: WARNING: main(): \" should follow this line." << std::endl;
  sf1.setMethod("main()");
  sf1.warn(max_chat) << "This was written to sf1.warn() after setMethod(...)" << std::endl;

  // Create a formatter with a single prefix.
  StreamFormatter sf2("AClassName", "", max_chat);
  std_os << "Two lines with a prefix of \"test_st_stream: WARNING: AClassName: \" should follow this line." << std::endl;
  sf2.warn(max_chat + 1) << "THIS SHOULD NOT APPEAR! This was written to sf2.warn(" << max_chat + 1 << ")." << std::endl;
  sf2.warn(0) << "This was written to sf2.warn(0), and should always appear." << std::endl;
  sf2.warn() << "This was written to sf2.warn() with a default chatter of " << max_chat << std::endl;

  // Now include a method name in the warning.
  std_os << "A line with a prefix of \"test_st_stream: WARNING: AClassName::aMethod(int): \" should follow this line." <<
    std::endl;
  sf2.setMethod("aMethod(int)");
  sf2.warn() << "This was written to sf2.warn() after setMethod(...)" << std::endl;

  // Test debug statements, which should be issued no matter what if debugging is enabled.
  std_os << "A line with prefix \"test_st_stream: DEBUG: AClassName::aMethod(int): \" should follow this line." << std::endl;
  sf2.debug() << Chat(std::numeric_limits<unsigned int>::max()) << "This was written to sf2.debug() with highest possible chat." <<
    std::endl;

  // Test info method with debugging enabled.
  std_os << "A line with prefix \"test_st_stream: INFO: AClassName::aMethod(int): \" should follow this line." << std::endl;
  sf2.info(0) << "This was written to sf2.info(0), and should always appear." << std::endl;

  // Test err method with debugging enabled.
  std_os << "A line with prefix \"test_st_stream: ERROR: AClassName::aMethod(int): \" should follow this line." << std::endl;
  sf2.err() << Chat(std::numeric_limits<unsigned int>::max()) <<
    "This was written to sf2.err(), and should always appear despite its highest possible chatter level." << std::endl;

  // Test out method with debugging enabled.
  std_os << "A line with prefix \"test_st_stream: \" should follow this line." << std::endl;
  sf2.out() << Chat(std::numeric_limits<unsigned int>::max()) <<
    "This was written to sf2.out(), and should always appear despite its highest possible chatter level." << std::endl;

  // Turn off debug statements. Verify that debug statements no longer appear no matter what.
  sf2.setDebugMode(false);
  sf2.debug() << Chat(0) << "THIS SHOULD NOT APPEAR! This was written to sf2.debug() after setDebugMode(false)." <<
    std::endl;

  // Test info method with debugging disabled.
  std_os << "A line with prefix \"test_st_stream: INFO: \" should follow this line." << std::endl;
  sf2.info(0) << "This was written to sf2.info(0), and should always appear." << std::endl;

  // Test err method with debugging disabled.
  std_os << "A line with prefix \"test_st_stream: ERROR: \" should follow this line." << std::endl;
  sf2.err() << Chat(std::numeric_limits<unsigned int>::max()) <<
    "This was written to sf2.err(), and should always appear despite its highest possible chatter level." << std::endl;

  // Test out method with debugging disabled.
  std_os << "A line with prefix \"test_st_stream: \" should follow this line." << std::endl;
  sf2.out() << Chat(std::numeric_limits<unsigned int>::max()) <<
    "This was written to sf2.out(), and should always appear despite its highest possible chatter level." << std::endl;

  return 0;
}
