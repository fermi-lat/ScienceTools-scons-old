/** \file Ref.h

    \brief Utilities to streamline access to cells of data inside a table.

    \author James Peachey, HEASARC
*/
#ifndef table_Ref_h
#define table_Ref_h

#include "table/table_types.h"
#include "table/Table.h"

namespace table {

  /** \class Ref

      \brief Adaptor class which provides a convenient read/write interface to cells of data inside a table.
  */
  template <typename T>
  class Ref {
    public:
      /** \brief Construct a Ref object which refers to the given Cell object.
          \param cell The referent Cell object.
      */
      Ref(Table::Cell & cell): m_cell(&cell) {}

      /** \brief Assignment from Cell. This changes which Cell object the Ref refers to.
          \param cell The new referent Cell object.
      */
      Ref & operator =(Table::Cell & cell) { m_cell = &cell; }

      /** \brief Assignment from templated parameter type. This will write the assigned value into the
          cell to which this object refers.
          \param data The source value for the assignment.
      */
      Ref & operator =(T data) { /* m_cell->write(data); */ return *this; }

      /** \brief Retrieve the current templated parameter data value of this object.
      */
      operator T () const { T data; m_cell->read(data); return data; }

    private:
      Table::Cell * m_cell;
  };

}

#endif
