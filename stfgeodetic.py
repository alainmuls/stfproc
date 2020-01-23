#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import sys
from termcolor import colored
import numpy as np
import pandas as pd
import logging
import utm as UTM

import am_config as amc
from ampyutils import amutils
from GNSS import gpstime
from SSN import signal_types as ssnst
from plot import plotcoords

__author__ = 'amuls'


def treatCmdOpts(argv):
    """
    Treats the command line options and sets the global variables according to the CLI args

    :param argv: the options (without argv[0])
    :type argv: list of string
    """
    helpTxt = os.path.basename(__file__) + ' reads in a sbf2stf converted SBF Geodetic-v2 file and make UTM plots'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-d', '--dir', help='Directory of SBF file (defaults to .)', required=False, default='.', type=str)
    parser.add_argument('-f', '--files', help='Filename of PVTGeodetic_v2 file', required=True, type=str)
    parser.add_argument('-g', '--gnss', help='GNSS System Name', required=True, type=str)
    parser.add_argument('-m', '--marker', help='Geodetic coordinates (lat,lon,ellH) of reference point in degrees: ["50.8440152778" "4.3929283333" "151.39179"] for RMA, ["50.93277777", "4.46258333", "123"] for Peutie, default ["0", "0", "0"] means use mean position', nargs=3, type=str, required=False, default=["0", "0", "0"])

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    args = parser.parse_args()

    return args.dir, args.files, args.gnss, args.marker, args.logging


def checkExistenceArgs(stfDir: str, stfFile: str, logger: logging.Logger) -> str:
    """
    checks if dir and stfFile are accessible
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to the directory stfDir if it exists
    wdir = os.getcwd()
    if stfDir is not '.':
        wdir = os.path.normpath(os.path.join(wdir, stfDir))
    logger.info('{func:s}: working diretory is {dir:s}'.format(func=cFuncName, dir=wdir))

    if not os.path.exists(wdir):
        logger.error('{func:s}: directory {dir:s} does not exists.'.format(func=cFuncName, dir=colored(wdir, 'red')))
        sys.exit(amc.E_DIR_NOT_EXIST)
    else:
        os.chdir(wdir)
        logger.info('{func:s}: changed to directory {dir:s}'.format(func=cFuncName, dir=wdir))

    # check if the given STF stfFile are accessible
    if not os.access(stfFile, os.R_OK):
        logger.error('{func:s}: STF file {file:s} is not accessible.'.format(func=cFuncName, file=colored(stfFile, 'red')))
        sys.exit(amc.E_FILE_NOT_ACCESSIBLE)

    return wdir


def readSTFGeodetic(stfFile: str, logger: logging.Logger) -> pd.DataFrame:
    """
    read in the STF Geodetic_v2 file using included header information
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # read in the file with in
    logger.info('{func:s}: reading file {file:s}'.format(file=stfFile, func=cFuncName))
    dfSTF = pd.read_csv(stfFile, sep=',', skiprows=range(1, 2))
    amutils.logHeadTailDataFrame(df=dfSTF, dfName=dSTF['stf'], callerName=cFuncName, logger=logger)
    dfSTF.dropna(subset=['Latitude[rad]', 'Longitude[rad]'], inplace=True)
    amutils.logHeadTailDataFrame(df=dfSTF, dfName=dSTF['stf'], callerName=cFuncName, logger=logger)
    dfSTF.reset_index(inplace=True)

    # convert lat/lon to degrees
    dfSTF['lat'] = np.degrees(dfSTF['Latitude[rad]'])
    dfSTF['lon'] = np.degrees(dfSTF['Longitude[rad]'])
    # convert the GPS time to UTC
    dfSTF['time'] = dfSTF.apply(lambda x: gpstime.UTCFromWT(x['WNc[week]'], x['TOW[s]']), axis=1)

    # add UTM coordinates
    dfSTF['UTM.E'], dfSTF['UTM.N'], dfSTF['UTM.Z'], dfSTF['UTM.L'] = UTM.from_latlon(dfSTF['lat'].to_numpy(), dfSTF['lon'].to_numpy())

    # calculate distance to st-Niklass 51.1577189  4.1915975
    dfSTF['dist'] = np.linalg.norm(dfSTF[['UTM.E', 'UTM.N']].sub(np.array([dSTF['marker']['UTM.E'], dSTF['marker']['UTM.N']])), axis=1)
    # dfSTF['dist2'] = np.linalg.norm([dfSTF['UTM.E'].iloc[0], dfSTF['UTM.N'].iloc[0]] - [dSTF['marker']['UTM.E'], dSTF['marker']['UTM.N']])

    # add info to dSTF about time
    dTime = {}
    dTime['epochs'] = dfSTF.shape[0]
    dTime['date'] = dfSTF.time.iloc[0].strftime('%d %b %Y')
    dTime['start'] = dfSTF.time.iloc[0].strftime('%H:%M:%S')
    dTime['end'] = dfSTF.time.iloc[-1].strftime('%H:%M:%S')
    dSTF['Time'] = dTime

    # add info to dSTF about #epochs
    dSTF['#epochs'] = dfSTF.shape[0]

    # add info to dSTF about used signal types used
    dST = {}
    sigTypes = dfSTF.SignalInfo.unique()
    logger.info('{func:s}: found nav-signals {sigt!s}'.format(sigt=sigTypes, func=cFuncName))
    for i, sigType in enumerate(sigTypes):
        logger.debug('{func:s}: searching name for sig-type {st!s}'.format(st=sigType, func=cFuncName))

        sigTypeNames = []

        for k, v in ssnst.dSigType.items():
            # logger.debug('{func:s}: checking presence of signal {sig!s}'.format(sig=v, func=cFuncName))
            # logger.debug('{func:s}: bin(sigType) = {st!s}'.format(st=bin(sigType), func=cFuncName))
            # logger.debug('{func:s}: bin(0b1 << k) = {ssnst!s}'.format(ssnst=bin(0b1 << k), func=cFuncName))
            # logger.debug('{func:s}: bin(bin(sigType) & bin(0b1 << k)) = {binops!s})'.format(binops=bin(sigType & (0b1 << k)), func=cFuncName))
            # logger.debug('{func:s}: binary check sigtype = {st!s} - ssn = {ssnst!s} operator and = {opsbin!s}'.format(st=bin(sigType), ssnst=bin(0b1 << k), opsbin=bin(sigType & (0b1 << k)), func=cFuncName))
            # logger.debug('-' * 10)

            if (sigType & (0b1 << k)) != 0:
                logger.info('{func:s}: found signal {ssnst:s}'.format(ssnst=v, func=cFuncName))
                # add name to the used signal types
                sigTypeNames.append(v[4:])

        # add signal to the dST dict
        dST[sigType] = sigTypeNames

        # nrBitsSet = ssnst.countSetBits(sigType)
        # lst1Bits = ssnst.findAllSetBits(sigType, nrBitsSet)

        # # get the name of the signals
        # stName = ssnst.dSigType[lst1Bits[0]]
        # if nrBitsSet > 1:
        #     for j in lst1Bits[1:]:
        #         stName += '+' + ssnst.dSigType[j]
        # dST[sigType] = stName

    dSTF['signals'] = dST
    logger.info('{func:s}: found signals {signals!s}'.format(signals=dSTF['signals'], func=cFuncName))

    # find out what PVT error codess we have
    errCodes = list(set(dfSTF.Error.unique()))
    dSTF['errCodes'] = errCodes
    logger.info('{func:s}: found error codes {errc!s}'.format(errc=errCodes, func=cFuncName))

    # inform user
    logger.info('{func:s}: read STF file {file:s}, added UTM coordiantes and GNSS time'.format(file=stfFile, func=cFuncName))

    return dfSTF


def main(argv):
    """
    creates a combined SBF file from hourly or six-hourly SBF files
    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    dirSTF, fileSTF, GNSSsyst, crdMarker, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(os.path.basename(__file__), dir=dirSTF, logLevels=logLevels)

    # check if arguments are accepted
    workDir = checkExistenceArgs(stfDir=dirSTF, stfFile=fileSTF, logger=logger)

    # create dictionary with the current info
    global dSTF
    dSTF = {}
    dSTF['dir'] = workDir
    dSTF['gnss'] = GNSSsyst
    dSTF['stf'] = fileSTF

    # set the reference point
    dMarker = {}
    dMarker['lat'], dMarker['lon'], dMarker['ellH'] = map(float, crdMarker)
    if [dMarker['lat'], dMarker['lon'], dMarker['ellH']] == [0, 0, 0]:
        dMarker['lat'] = dMarker['lon'] = dMarker['ellH'] = np.NaN
        dMarker['UTM.E'] = dMarker['UTM.N'] = np.NaN
        dMarker['UTM.Z'] = dMarker['UTM.L'] = ''
    else:
        dMarker['UTM.E'], dMarker['UTM.N'], dMarker['UTM.Z'], dMarker['UTM.L'] = UTM.from_latlon(dMarker['lat'], dMarker['lon'])

    logger.info('{func:s}: marker coordinates = {crd!s}'.format(func=cFuncName, crd=dMarker))
    amc.dRTK['marker'] = dMarker

    # # add jammer location coordinates
    # dMarker = {}
    # dMarker['geod'] = {}
    # dMarker['geod']['lat'] = 51.19306  # 51.193183
    # dMarker['geod']['lon'] = 4.15528  # 4.155056
    # dMarker['UTM'] = {}
    # dMarker['UTM.E'], dMarker['UTM.N'], dMarker['UTM.Z'], dMarker['UTM.L'] = utm.from_latlon(dMarker['geod']['lat'], dMarker['geod']['lon'])
    dSTF['marker'] = dMarker

    # read in the STF file using included header information
    dfGeod = readSTFGeodetic(stfFile=fileSTF, logger=logger)
    amutils.logHeadTailDataFrame(df=dfGeod, dfName=dSTF['stf'], callerName=cFuncName, logger=logger)

    # save to cvs file
    dSTF['csv'] = os.path.splitext(dSTF['stf'])[0] + '.csv'
    dfGeod.to_csv(dSTF['csv'])

    # plot trajectory
    logger.info('{func:s}: information:\n{dict!s}'.format(dict=amutils.pretty(dSTF), func=cFuncName))
    plotcoords.plotUTMSuppressed(dStf=dSTF, dfCrd=dfGeod[['time', 'UTM.E', 'UTM.N', 'Error']], logger=logger)

    # plot the UTM coordinates and #SVs
    plotcoords.plotUTMCoords(dStf=dSTF, dfCrd=dfGeod[['time', 'UTM.E', 'UTM.N', 'Height[m]', 'NrSV', 'SignalInfo', 'dist', '2D/3D']], logger=logger)
    # plot trajectory
    plotcoords.plotUTMScatter(dStf=dSTF, dfCrd=dfGeod[['time', 'UTM.E', 'UTM.N', 'SignalInfo', '2D/3D']], logger=logger)

    logger.info('{func:s}: information:\n{dict!s}'.format(dict=amutils.pretty(dSTF), func=cFuncName))


if __name__ == "__main__":
    main(sys.argv)
