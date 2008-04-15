# $Id$
#
SIMPLE  =                    T / Dummy Created by MWRFITS v1.4a
BITPIX  =                    8 / Dummy primary header created by MWRFITS
NAXIS   =                    0 / No data is associated with this header
EXTEND  =                    T / Extensions may (will!) be present
ORIGIN  = 'LISOC'              / Name of organization making this file
END

XTENSION= 'BINTABLE'           / binary table extension                        
BITPIX  =                    8 / 8-bit bytes                                   
NAXIS   =                    2 / 2-dimensional binary table                    
NAXIS1  =                15224 / width of table in bytes                       
NAXIS2  =                    1 / number of rows in table                       
PCOUNT  =                    0 / size of special data area                     
GCOUNT  =                    1 / one data group (required keyword)             
TFIELDS =                   10 / number of fields in each row                  
EXTNAME = 'ENERGY DISPERSION'  / name of this binary table extension
ORIGIN  = 'LISOC'              / name of organization making this file
DATE    =                      / file creation date (YYYY-MM-DDThh:mm:ss UT)
TTYPE1  = 'ENERG_LO'           /                                               
TFORM1  = '54E     '           /                                               
TUNIT1  = 'MeV     '           /                                               
TTYPE2  = 'ENERG_HI'           /                                               
TFORM2  = '54E     '           /                                               
TUNIT2  = 'MeV     '           /                                               
TTYPE3  = 'CTHETA_LO'          /                                               
TFORM3  = '32E     '           /                                               
TUNIT3  = '        '           /
TTYPE4  = 'CTHETA_HI'          /                                               
TFORM4  = '32E     '           /                                               
TUNIT4  = '        '           /
TTYPE5  = 'NORM   '           /                                               
TFORM5  = '1728E   '           /                                               
TUNIT5  = '        '           /                                               
TDIM5   = '( 54, 32)'
TTYPE6  = 'LS1     '           /                                               
TFORM6  = '1728E   '           /                                               
TUNIT6  = '        '           /                                               
TDIM6   = '( 54, 32)'
TTYPE7  = 'RS1     '           /                                               
TFORM7  = '1728E   '           /                                               
TUNIT7  = '        '           /                                               
TDIM7   = '( 54, 32)'
TTYPE8  = 'BIAS      '         /                                               
TFORM8  = '1728E   '           /                                               
TUNIT8  = '        '           /                                               
TDIM8   = '( 54, 32)'
TTYPE9  = 'LS2     '           /                                               
TFORM9  = '1728E   '           /                                               
TUNIT9  = '        '           /                                               
TDIM9   = '( 54, 32)'
TTYPE10 = 'RS2     '           /                                               
TFORM10 = '1728E   '           /                                               
TUNIT10 = '        '           /                                               
TDIM10  = '( 54, 32)'
TELESCOP= 'GLAST   '           /                                               
INSTRUME= 'LAT     '           /                                               
DETNAM  = 'FRONT   '
HDUCLASS= 'OGIP    '           /                                               
HDUDOC  = 'CAL/GEN/92-019'     /                                               
HDUCLAS1= 'RESPONSE'           /                                               
HDUCLAS2= 'EDISP   '           /                                               
HDUVERS = '1.0.0   '           /                                               
EARVERSN= '1992a   '           /                                               
1CTYP5  = 'ENERGY  '           / Always use log(ENERGY) for interpolation
2CTYP5  = 'COSTHETA'           / Off-axis angle cosine
CREF5   = '(ENERG_LO:ENERG_HI,CTHETA_LO:CTHETA_HI)' /                          
CSYSNAME= 'XMA_POL '           /                                               
CCLS0001= 'BCF     '           /                                               
CDTP0001= 'DATA    '           /                                               
CCNM0001= 'EDISP   '           /                                               
CBD10001= 'VERSION(HANDOFF)'   /
CBD20001= 'CLASS(FRONTA)'      /
CBD30001= 'ENERG(18-560000)MeV' /
CBD40001= 'CTHETA(0.2-1)'      /
CBD50001= 'PHI(0-360)deg'      /
CBD60001= 'NONE'               /
CBD70001= 'NONE'               /
CBD80001= 'NONE'               /
CBD90001= 'NONE'               /
CVSD0001= '2007-01-17'         / Dataset validity start date (UTC)
CVST0001= '00:00:00'           /                                               
CDES0001= 'GLAST LAT ENERGY DISPERSION' /
END
