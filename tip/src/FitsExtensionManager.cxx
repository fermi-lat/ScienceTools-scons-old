/** \file FitsExtensionManager.cxx

    \brief Implementation of utilities to help manage FITS specific table access.

    \author James Peachey, HEASARC
*/

#include <cctype>
#include <sstream>

#include "FitsExtensionManager.h"
#include "tip/HeaderData.h"
#include "tip/IData.h"
#include "tip/TabularData.h"
#include "tip/TipException.h"

namespace tip {

  // Create a FITS file using a template.
  void FitsExtensionManager::createFile(const std::string & file_name, const std::string & template_name) {
    // Concatenate the file name with the template name:
    std::ostringstream s;
    s << "!" << file_name << "(" << template_name << ")";
    std::string full_name = s.str();

    fitsfile * fp = 0;
    int status = 0;

    // Create the file, and complain if it doesn't work:
    fits_create_file(&fp, const_cast<char *>(full_name.c_str()), &status);
    if (0 != status) throw TipException(std::string("Unable to create file named \"") + full_name + '"');

    // Close the file; not interested in it anymore.
    fits_close_file(fp, &status);
  }

  // Construct without opening the file.
  FitsExtensionManager::FitsExtensionManager(const std::string & file_name, const std::string & ext_name,
    const std::string & filter): m_file_name(file_name), m_ext_name(ext_name), m_filter(filter), m_col_name_lookup(),
    m_col_num_lookup(), m_num_records(0), m_fp(0), m_header(0), m_data(0), m_is_table(false) { open(); }

  // Close file automatically while destructing.
  FitsExtensionManager::~FitsExtensionManager() { delete m_data; delete m_header; close(); }

  IHeaderData * FitsExtensionManager::getHeaderData() {
    if (!m_header) m_header = new HeaderData<FitsExtensionManager>(*this);
    return m_header;
  }

  ITabularData * FitsExtensionManager::getTabularData() {
    ITabularData * retval = 0;
    if (!m_data) {
      retval = new TabularData<FitsExtensionManager>(*this);
      m_data = retval;
    }
    return retval;
  }

  // Subclasses call this to open the file and position it to the desired extension.
  void FitsExtensionManager::open() {
    if (!m_fp) {
      fitsfile * fp = 0;
      int status = 0;

      // Construct the full name of the file from file name [extension] [filter] (if any):
      std::ostringstream s;
      s << m_file_name;
      if (!m_ext_name.empty()) s << "[" << m_ext_name << "]";
      if (!m_filter.empty()) s << "[" << m_filter << "]";
      std::string file_name = s.str();

      // Open the fits file.
      fits_open_file(&fp, const_cast<char *>(file_name.c_str()), READWRITE, &status);

      if (0 != status) {
        // TODO 9. 4/2/2004: Bug in cfitsio 2.48: Check for it and warn about it. The bug causes
        // the parser not to move to the correct extension.
        float cfitsio_version = 0.;
        fits_get_version(&cfitsio_version);
        // This is surreal. A FLOATING POINT VERSION NUMBER! Checking for == doesn't work -- I tried it.
        if (2.47 < cfitsio_version && 2.49 > cfitsio_version)
          throw TipException(std::string("WARNING: there is a known bug in Cfitsio 2.48's extended "
            "syntax parser!\nCould not open FITS file ") + file_name);
        throw TipException(std::string("Could not open FITS file \"") + file_name + '"');
      }

      // Success: save the pointer.
      m_fp = fp;

      // Check whether the file pointer is pointing at a table:
      int hdu_type = 0;
      fits_get_hdu_type(m_fp, &hdu_type, &status);
      if (0 != status) {
        close(status);
        throw TipException(formatWhat("Could not determine the type of the HDU"));
      }
      if (ASCII_TBL == hdu_type || BINARY_TBL == hdu_type) {
        m_is_table = true;

        // If this is a table, perform other table-specific initializations:
        openTable();
      }
    }
  }

  // Close file.
  void FitsExtensionManager::close(int status) {
    if (m_fp) fits_close_file(m_fp, &status);
    m_fp = 0;
  }

  void FitsExtensionManager::openTable() {
    int status = 0;
    int column_status = 0;
    long nrows = 0;

    // Read the number of rows present in the table.
    fits_get_num_rows(m_fp, &nrows, &status);

    // Check for success and if not, do not continue.
    if (0 != status) {
      close(status);
      throw TipException(formatWhat("Cannot get number of rows"));
    }

    // Save the number of rows.
    m_num_records = (Index_t) nrows;

    char * match_all = "*";
    char name[128]; // jp fix this: what is the maximum length of a FITS column name?
    int col_num;
    int type_code;
    long repeat;

    // Iterate over columns, putting the name of each in the column container.
    while (COL_NOT_FOUND != column_status) {
      *name = '\0';
      col_num = 0;
      type_code = 0;
      repeat = 0;
      // Get each column's name.
      fits_get_colname(m_fp, CASEINSEN, match_all, name, &col_num, &column_status);
      if (0 == column_status || COL_NOT_UNIQUE == column_status) {
        // Also get its type and repeat count.
        fits_get_coltype(m_fp, col_num, &type_code, &repeat, 0, &status);
        if (0 != status) {
          close(status);
          std::ostringstream s;
          s << "Could not get type information for column number " << col_num;
          throw TipException(formatWhat(s.str()));
        }

        // Save values iff successful getting all the information.
        // Convert name to lover case.
        for (char * itor = name; *itor; ++itor) *itor = tolower(*itor);
        m_col_name_lookup[name].m_name = name;
        m_col_name_lookup[name].m_col_num = col_num;
        m_col_name_lookup[name].m_repeat = repeat;
        m_col_name_lookup[name].m_type_code = type_code;
        m_col_num_lookup[col_num].m_name = name;
        m_col_num_lookup[col_num].m_col_num = col_num;
        m_col_num_lookup[col_num].m_repeat = repeat;
        m_col_num_lookup[col_num].m_type_code = type_code;
      }
    }
  }

  Index_t FitsExtensionManager::getNumRecords() const {
    if (!m_is_table) throw TipException(formatWhat("getNumRecords called, but object is not a table"));
    return m_num_records;
  }

  // Resize the FITS table, adding or deleting rows as necessary.
  void FitsExtensionManager::setNumRecords(Index_t num_records) {
    if (!m_is_table) throw TipException(formatWhat("getNumRecords called, but object is not a table"));
    int status = 0;
    if (m_num_records < num_records) {
      fits_insert_rows(m_fp, m_num_records, num_records - m_num_records, &status);
      if (0 != status) throw TipException("Could not insert rows in FITS table");
      m_num_records = num_records;
    } else if (m_num_records > num_records) {
      fits_delete_rows(m_fp, num_records + 1, m_num_records - num_records, &status);
      if (0 != status) throw TipException("Could not delete rows from FITS table");
      m_num_records = num_records;
    }
  }

  FieldIndex_t FitsExtensionManager::getFieldIndex(const std::string & field_name) const {
    if (!m_is_table) throw TipException(formatWhat("getNumRecords called, but object is not a table"));

    // Copy field name and make it lowercase.
    std::string tmp = field_name;
    for (std::string::iterator itor = tmp.begin(); itor != tmp.end(); ++itor) *itor = tolower(*itor);

    // Find (lowercased) field_name in container of columns. Complain if not found.
    std::map<std::string, ColumnInfo>::const_iterator itor = m_col_name_lookup.find(tmp);
    if (itor == m_col_name_lookup.end())
      throw TipException(formatWhat(std::string("Could not get field index for field ") + field_name));

    // Get the number of the column.
    return itor->second.m_col_num;
  }

  Index_t FitsExtensionManager::getFieldNumElements(FieldIndex_t field_index, Index_t record_index) const {
    if (!m_is_table) throw TipException(formatWhat("getNumRecords called, but object is not a table"));

    // Find field_index in container of columns. Complain if not found.
    std::map<FieldIndex_t, ColumnInfo>::const_iterator itor = m_col_num_lookup.find(field_index);
    if (itor == m_col_num_lookup.end()) {
      std::ostringstream s;
      s << "Could not get number of elements in field number " << field_index;
      throw TipException(formatWhat(s.str()));
    }
    const ColumnInfo & info = itor->second;
    long repeat = 0;
    if (0 <= info.m_type_code) {
      // Constant length column.
      repeat = info.m_repeat;
    } else {
      // Variable length column.
      int status = 0;
      fits_read_descript(m_fp, field_index, record_index + 1, &repeat, 0, &status);
      if (0 != status) {
        std::ostringstream s;
        s << "Could not get number of elements from variable vector column " << info.m_name << ", row " << record_index;
        throw TipException(formatWhat(s.str()));
      }
    }
    return repeat;
  }

  std::string FitsExtensionManager::formatWhat(const std::string & msg) const {
    std::ostringstream msg_str;
    msg_str << msg;
    if (!m_ext_name.empty()) msg_str << " in extension \"" << m_ext_name << '"';
    msg_str << " in file \"" << m_file_name << '"';
    return msg_str.str();
  }

}
