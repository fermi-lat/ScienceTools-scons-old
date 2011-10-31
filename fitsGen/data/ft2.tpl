SIMPLE      = T                           / file does conform to FITS standard
BITPIX      = 8                           / number of bits per data pixel
NAXIS       = 0                           / number of data axes
EXTEND      = T                           / FITS dataset may contain extensions
CHECKSUM    =                             / checksum for entire HDU
TELESCOP    = 'GLAST'                     / name of telescope generating data
INSTRUME    = 'LAT'                       / name of instrument generating data
EQUINOX     = 2000.0                      / equinox for ra and dec
RADECSYS    = 'FK5'                       / world coord. system for this file (FK5 or FK4)
DATE        =                             / file creation date (YYYY-MM-DDThh:mm:ss UT)
DATE-OBS    =                             / START date and time of the observation (UTC)
DATE-END    =                             / end date and time of the observation (UTC)
TSTART      =                                / mission time of the START of the observation
TSTOP       =                                / mission time of the end of the observation
TIMESYS     = 'TT'                           / type of time system that is used
TIMEUNIT    = 's'                            / units for TSTART and TSTOP keywords
GPS_OUT     = F                              / whether GPS time was unavailable at any time during this interval
MJDREFI     = 51910.                         / Integer part of MJD corresponding to SC clock START
MJDREFF     = 7.428703703703703D-4           / Fractional part of MJD corresponding to SC clock START
OBSERVER    = 'Peter Michelson'              / GLAST/LAT PI
FILENAME    =                             / name of this file
ORIGIN      = 'LISOC'                     / name of organization making file
#AUTHOR      =                             / name of person responsible for file generation
CREATOR     =                             / software and version creating file
VERSION     = 1                           / release version of the file
#SOFTWARE    =                             / version of the processing software
PROC_VER    = 1                              / processing version of this file 
END

XTENSION     = 'BINTABLE'                  / binary table extension
BITPIX       = 8                           / 8-bit bytes
NAXIS        = 2                           / 2-dimensional binary table
NAXIS1       =                             / width of table in bytes
NAXIS2       =                             / number of rows in table
PCOUNT       =                             / size of special data area
GCOUNT       = 1                           / one data group (required keyword)
TFIELDS      =                             / number of fields in each row
CHECKSUM     =                             / checksum for entire HDU
DATASUM      =                             / checksum for data table
TELESCOP     = 'GLAST'                     / name of telescope generating data
INSTRUME     = 'LAT'                       / name of instrument generating data
EQUINOX      = 2000.0                      / equinox for ra and dec
RADECSYS     = 'FK5'                       / world coord. system for this file (FK5 or FK4)
DATE         =                             / file creation date (YYYY-MM-DDThh:mm:ss UT)
DATE-OBS     =                             / START date and time of the observation (UTC)
DATE-END     =                             / end date and time of the observation (UTC)
OBSERVER    = 'Peter Michelson'            / GLAST/LAT PI
ORIGIN      = 'LISOC'                      / name of organization making file
EXTNAME      = 'SC_DATA'                   / name of this binary table extension
TSTART       =                             / mission time of the START of the observation
TSTOP        =                             / mission time of the end of the observation
MJDREFI      = 51910.                      / Integer part of MJD corresponding to SC clock START
MJDREFF      = 7.428703703703703D-4        / Fractional part of MJD corresponding to SC clock START
TIMEUNIT     = 's'                         / units for the time related keywords
TIMEZERO     = 0.0                         / clock correction
TIMESYS      = 'TT'                        / type of time system that is used
TIMEREF      = 'LOCAL'                     / reference frame used for times
TASSIGN      = 'SATELLITE'                 / location where time assignment performed
CLOCKAPP     = F                           / whether a clock drift correction has been applied
GPS_OUT      = F                           / whether GPS time was unavailable at any time during this interval
TTYPE1       = 'START'                     / STARTing time of interval (Mission Elapsed Time)
TFORM1       = 'D'                         / data format of field: 8-byte DOUBLE
TUNIT1       = 's'                         / physical unit of field
TLMIN1       = 0.0                         / minimum value
TLMAX1       = 1.0D+10                     / maximum value
TTYPE2       = 'STOP'                      / ending time of interval (Mission Elapsed Time)
TFORM2       = 'D'                         / data format of field: 8-byte DOUBLE
TUNIT2       = 's'                         / physical unit of field
TLMIN2       = 0.0                         / minimum value
TLMAX2       = 1.0D+10                     / maximum value
TTYPE3       = 'SC_POSITION'               / S/C position at START of interval (x,y,z inertial coordinates)
TFORM3       = '3E'                        / data format of field: 4-byte REAL
TUNIT3       = 'm'                         / physical unit of field
TTYPE4       = 'LAT_GEO'                   / ground point latitude
TFORM4       = 'E'                         / data format of field: 4-byte REAL
TUNIT4       = 'deg'                       / physical unit of field
TLMIN4       = -90.0                       / minimum value
TLMAX4       = 90.0                        / maximum value
TTYPE5       = 'LON_GEO'                   / ground point longitude
TFORM5       = 'E'                         / data format of field: 4-byte REAL
TUNIT5       = 'deg'                       / physical unit of field
TLMIN5       = 0.0                         / minimum value
TLMAX5       = 360.0                       / maximum value
TTYPE6       = 'RAD_GEO'                   / S/C altitude
TFORM6       = 'D'                         / data format of field: 8-byte DOUBLE
TUNIT6       = 'm'                         / physical unit of field
TLMIN6       = 0.0                         / minimum value
TLMAX6       = 10000.0                     / maximum value
TTYPE7       = 'RA_ZENITH'                 / RA of zenith direction at START
TFORM7       = 'E'                         / data format of field: 8-byte DOUBLE
TUNIT7       = 'deg'                       / physical unit of field: dimensionless
TLMIN7       = 0.0                         / minimum value
TLMAX7       = 360.0                       / maximum value
TTYPE8       = 'DEC_ZENITH'                / Dec of zenith direction at START
TFORM8       = 'E'                         / data format of field: 4-byte REAL
TUNIT8       = 'deg'                       / physical unit of field: dimensionless
TLMIN8       = -90.0                       / minimum value
TLMAX8       = 90.0                        / maximum value
TTYPE9       = 'B_MCILWAIN'                / McIlwain B parameter, magnetic field
TFORM9       = 'E'                         / data format of field: 4-byte REAL
TUNIT9       = 'Gauss'                     / physical unit of field
TLMIN9       = 0.0                         / minimum value
TLMAX9       = 100.0                       / maximum value
TTYPE10      = 'L_MCILWAIN'                / McIlwain L parameter, distance
TFORM10      = 'E'                         / data format of field: 4-byte REAL
TUNIT10      = 'Earth_Radii'               / physical unit of field
TLMIN10      = 0.0                         / minimum value
TLMAX10      = 100.0                       / maximum value
TTYPE11      = 'GEOMAG_LAT'                / geomagnetic latitude
TFORM11      = 'E'                         / 4-byte real
TLMIN11      = -90.0                       / minimum value
TLMAX11      = 90.0                        / maximum value
TUNIT11      = 'deg'                       / physical unit
TTYPE12      = 'IN_SAA'                    / whether spacecraft was in SAA
TFORM12      = 'L'                         / data format of field: logical
TTYPE13      = 'RA_SCZ'                    / viewing direction at START (RA of S/C +z axis)
TFORM13      = 'E'                         / data format of field: 4-byte REAL
TUNIT13      = 'deg'                       / physical unit of field: dimensionless
TLMIN13      = 0.0                         / minimum value
TLMAX13      = 360.0                       / maximum value
TTYPE14      = 'DEC_SCZ'                   / viewing direction at START (Dec of S/C +z axis)
TFORM14      = 'E'                         / data format of field: 4-byte REAL
TUNIT14      = 'deg'                       / physical unit of field: dimensionless
TLMIN14      = -90.0                       / minimum value
TLMAX14      = 90.0                        / maximum value
TTYPE15      = 'RA_SCX'                    / viewing direction at START (RA of S/C +x axis)
TFORM15      = 'E'                         / data format of field: 4-byte REAL
TUNIT15      = 'deg'                       / physical unit of field: dimensionless
TLMIN15      = 0.0                         / minimum value
TLMAX15      = 360.0                       / maximum value
TTYPE16      = 'DEC_SCX'                   / viewing direction at START (Dec of S/C +x axis)
TFORM16      = 'E'                         / data format of field: 4-byte REAL
TUNIT16      = 'deg'                       / physical unit of field: dimensionless
TLMIN16      = -90.0                       / minimum value
TLMAX16      = 90.0                        / maximum value
TTYPE17      = 'RA_NPOLE'                  / RA of north orbital pole at START
TFORM17      = 'E'                         / data format of field: 4-byte REAL
TUNIT17      = 'deg'                       / physical unit of field: dimensionless
TLMIN17      = 0.0                         / minimum value
TLMAX17      = 360.0                       / maximum value
TTYPE18      = 'DEC_NPOLE'                 / Dec of north orbital pole at START
TFORM18      = 'E'                         / data format of field: 4-byte REAL
TUNIT18      = 'deg'                       / physical unit of field: dimensionless
TLMIN18      = -90.0                       / minimum value
TLMAX18      = 90.0                        / maximum value
TTYPE19      = 'ROCK_ANGLE'                / angle z axis from zenith (+=north) at START
TFORM19      = 'E'                         / data format of field: 4-byte REAL
TUNIT19      = 'deg'                       / physical unit of field: dimensionless
TLMIN19      = -180.0                      / minimum value
TLMAX19      = 180.0                       / maximum value
TTYPE20      = 'LAT_MODE'                  / attitude mode of LAT
TFORM20      = 'J'                         / data format of field: 4-byte signed INTEGER
TTYPE21      = 'LAT_CONFIG'                / flag for config. of LAT (1=nominal sci. config)
TFORM21      = 'B'                         / data format of field: byte 
TTYPE22      = 'DATA_QUAL'                 / flag for quality of data (1=nominal)
TFORM22      = 'I'                         / data format of field: 2-byte signed INTEGER
TTYPE23      = 'LIVETIME'                  / livetime
TFORM23      = 'D'                         / data format of field: 8-byte DOUBLE
TUNIT23      = 's'                         / physical unit of field
TTYPE24      = 'QSJ_1'                     / First component of SC attitude quaternion
TFORM24      = 'D'                         / 8-byte DOUBLE
TTYPE25      = 'QSJ_2'                     / Second component of SC attitude quaternion
TFORM25      = 'D'                         / 8-byte DOUBLE
TTYPE26      = 'QSJ_3'                     / Third component of SC attitude quaternion
TFORM26      = 'D'                         / 8-byte DOUBLE
TTYPE27      = 'QSJ_4'                     / Fourth component of SC attitude quaternion
TFORM27      = 'D'                         / 8-byte DOUBLE
TTYPE28      = 'RA_SUN'                    / RA of Sun
TFORM28      = 'E'                         / 4-byte REAL
TUNIT28      = 'deg'                       / physical unit of field: degrees
TLMIN28      = 0.0                         / minimum value
TLMAX28      = 360.0                       / maximum value
TTYPE29      = 'DEC_SUN'                   / DEC of Sun
TFORM29      = 'E'                         / 4-byte REAL
TUNIT29      = 'deg'                       / physical unit of field: degrees
TLMIN29      = -90.0                       / minimum value
TLMAX29      = 90.0                        / maximum value
