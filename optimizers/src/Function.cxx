/** 
 * @file Function.cxx
 * @brief Function class implementation
 * @author J. Chiang
 *
 * $Header$
 */

#include <iostream>
#include <sstream>

#include "xml/Dom.h"

#include "optimizers/Dom.h"
#include "optimizers/Function.h"

namespace optimizers {

void Function::setParam(const Parameter &param) throw(ParameterNotFound) {
   std::vector<Parameter>::iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (it->getName() == param.getName()) {
         (*it) = param;
         return;
      } 
   }
   throw(ParameterNotFound(param.getName(), getName(), 
                           "setParam(Parameter&)"));
}

double Function::getParamValue(const std::string &paramName) const
   throw(ParameterNotFound) {
   std::vector<Parameter>::const_iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (paramName == it->getName()) {
         return it->getValue();
      }
   }
   throw(ParameterNotFound(paramName, getName(), "getParamValue"));
}

Parameter Function::getParam(const std::string &paramName) const
   throw(ParameterNotFound) {
   std::vector<Parameter>::iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (paramName == it->getName()) {
         return *it;
      }
   }
   throw(ParameterNotFound(paramName, getName(), "getParam"));
}

void Function::setParamBounds(const std::string &paramName, double lower,
                              double upper) throw(ParameterNotFound) {
   std::vector<Parameter>::iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (paramName == it->getName()) {
         it->setBounds(lower, upper);
         return;
      }
   }
   throw(ParameterNotFound(paramName, getName(), "setParamBounds"));
}

void Function::setParamScale(const std::string &paramName, double scale) 
   throw(ParameterNotFound) {
   std::vector<Parameter>::iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (paramName == it->getName()) {
         it->setScale(scale);
         return;
      }
   }
   throw(ParameterNotFound(paramName, getName(), "setParamScale"));
}

void Function::setParamTrueValue(const std::string &paramName, 
                                 double paramValue) 
   throw(ParameterNotFound) {
   std::vector<Parameter>::iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (paramName == it->getName()) {
         it->setTrueValue(paramValue);
         return;
      }
   }
   throw(ParameterNotFound(paramName, getName(), "setParamTrueValue"));
}

void Function::setParamValues(const std::vector<double> &paramVec) 
   throw(Exception) {
   if (paramVec.size() != m_parameter.size()) {
      std::ostringstream errorMessage;
      errorMessage << "Function::setParamValues: "
                   << "The input vector size does not match "
                   << "the number of parameters.\n";
      throw(Exception(errorMessage.str()));
   } else {
      std::vector<double>::const_iterator it = paramVec.begin();
      setParamValues_(it);
   }
}
   
std::vector<double>::const_iterator Function::setParamValues_(
   std::vector<double>::const_iterator it) {
   for (unsigned int i = 0; i < m_parameter.size(); i++) 
      m_parameter[i].setValue(*it++);
   return it;
}

void Function::setParams(std::vector<Parameter> &params) 
   throw(Exception) {
   if (params.size() == m_parameter.size()) {
      m_parameter = params;
   } else {
      throw Exception
         ("Function::setParams: incompatible number of parameters.");
   }
}

void Function::setFreeParamValues(const std::vector<double> &paramVec) 
   throw(Exception) {
   if (paramVec.size() != getNumFreeParams()) {
      std::ostringstream errorMessage;
      errorMessage << "Function::setFreeParamValues: "
                   << "The input vector size " << paramVec.size() 
		   << "  does not match " << getNumFreeParams() << " , " 
                   << "the number of free parameters.\n";
      throw(Exception(errorMessage.str()));
   } else {
      std::vector<double>::const_iterator it = paramVec.begin();
      setFreeParamValues_(it);
   }
}

std::vector<double>::const_iterator Function::setFreeParamValues_(
   std::vector<double>::const_iterator it) {
   for (unsigned int i = 0; i < m_parameter.size(); i++) 
      if (m_parameter[i].isFree()) m_parameter[i].setValue(*it++);
   return it;
}

unsigned int Function::getNumFreeParams() const {
   int j = 0;
   for (unsigned int i = 0; i < m_parameter.size(); i++)
      j += m_parameter[i].isFree();
   return j;
}

void Function::getFreeParams(std::vector<Parameter> &params) const {
   if (!params.empty()) params.clear();
   
   for (unsigned int i = 0; i < m_parameter.size(); i++)
      if (m_parameter[i].isFree()) params.push_back(m_parameter[i]);
}

void Function::setFreeParams(std::vector<Parameter> &params) 
   throw(Exception) {
   if (params.size() == getNumFreeParams()) {
      int j = 0;
      for (unsigned int i = 0; i < m_parameter.size(); i++) {
         if (m_parameter[i].isFree()) {
            m_parameter[i] = params[j];
//             std::cerr << m_parameter[i].getName() << ": " 
//                       << m_parameter[i].getValue() << std::endl;
            j++;
         }
      }
   } else {
      throw(Exception(
               "Function::setFreeParams: incompatible number of parameters."));
   }
}      

void Function::setParameter(const std::string &paramName, 
			    double paramValue,
                            int isFree) throw(ParameterNotFound) {
// check if parameter is present...
   for (unsigned int i=0; i < m_parameter.size(); i++) {
      if (paramName == m_parameter[i].getName()) {
         m_parameter[i].setValue(paramValue);
// and update the free state if asked (yes, a bit kludgy...)
         if (isFree > -1) m_parameter[i].setFree(isFree);
         return;
      }
   }
   throw(ParameterNotFound(paramName, getName(), "setParameter"));
}

void Function::addParam(const std::string &paramName,
			double paramValue, 
			bool isFree) throw(Exception) {

// Check if paramName is already present.
   for (unsigned int i=0; i < m_parameter.size(); i++) {
      if (paramName == m_parameter[i].getName()) {
         std::ostringstream errorMessage;
         errorMessage << "Function::addParam: "
                      << "This parameter name already exists: "
                      << paramName << "; "
                      << "you can't add another one.\n";
         throw(Exception(errorMessage.str()));
      }
   }
// If there's room, add this onto the vector.
   if (m_parameter.size() < m_maxNumParams) {
      Parameter my_param(paramName, paramValue, isFree);
      m_parameter.push_back(my_param);
   } else {
      std::ostringstream errorMessage;
      errorMessage << "Function::addParam: " 
                   << "Can't add parameter " << paramName << ". "
                   << "The parameter list is full at " 
                   << m_maxNumParams << ".\n";
      throw(Exception(errorMessage.str()));
   }
}

void Function::addParam(const Parameter &param) throw(Exception) {
   std::vector<Parameter>::const_iterator it = m_parameter.begin();
   for (; it != m_parameter.end(); it++) {
      if (param.getName() == it->getName()) {
         std::ostringstream errorMessage;
         errorMessage << "Function::addParam: "
                      << "This parameter name already exists: "
                      << param.getName() << "; "
                      << "you can't add another one.\n";
         throw(Exception(errorMessage.str()));
      } 
   }
   if (m_parameter.size() < m_maxNumParams) {
         m_parameter.push_back(param);
   } else {
      std::ostringstream errorMessage;
      errorMessage << "Can't add parameter " << param.getName() << "; "
                   << "the parameter list is full at " 
                   << m_maxNumParams << ".\n";
      throw(Exception(errorMessage.str()));
   }
}

void Function::fetchParamValues(std::vector<double> &values,
                                bool getFree) const {
   if (!values.empty()) values.clear();

   for (unsigned int i = 0; i < m_parameter.size(); i++) {
      if (!getFree || m_parameter[i].isFree())
         values.push_back(m_parameter[i].getValue());
   }
}

void Function::fetchParamNames(std::vector<std::string> &names,
                               bool getFree) const {
   if (!names.empty()) names.clear();

   for (unsigned int i = 0; i < m_parameter.size(); i++) {
      if (!getFree || m_parameter[i].isFree())
         names.push_back(m_parameter[i].getName());
   }
}

void Function::fetchDerivs(Arg &x, std::vector<double> &derivs, 
                           bool getFree) const {
   if (!derivs.empty()) derivs.clear();

   for (unsigned int i = 0; i < m_parameter.size(); i++) {
      if (!getFree || m_parameter[i].isFree())
         derivs.push_back(derivByParam(x, m_parameter[i].getName()));
   }
}

void Function::appendParamDomElements(DOMDocument * doc, DOMNode * node) {
   std::vector<Parameter>::iterator paramIt = m_parameter.begin();
   for ( ; paramIt != m_parameter.end(); ++paramIt) {
      DOMElement * paramElt = paramIt->createDomElement(doc);
//      node->appendChild(reinterpret_cast<DOMNode *>(paramElt));
      Dom::appendChild(node, paramElt);
   }
}

void Function::setParams(const DOMElement * elt) {
   std::vector<DOMElement *> parElts;
   xml::Dom::getChildrenByTagName(elt, "parameter", parElts);
   for (unsigned int i = 0; i < parElts.size(); i++) {
      std::string name = xml::Dom::getAttribute(parElts[i], "name");
      for (unsigned int j = 0; j < m_parameter.size(); j++) {
         if (m_parameter[j].getName() == name) {
            m_parameter[j].extractDomData(parElts[i]);
            break;
         }
      }
   }
}

} // namespace optimizers
