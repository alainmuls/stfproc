#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import sys
from termcolor import colored
import numpy as np
import pandas as pd
import logging
import utm

import am_config as amc
from ampyutils import amutils
from GNSS import gpstime
from SSN import signal_types as ssnst
from plot import plotagc

__author__ = 'amuls'


def treatCmdOpts(argv):
    """
    Treats the command line options and sets the global variables according to the CLI args

    :param argv: the options (without argv[0])
    :type argv: list of string
    """
    helpTxt = os.path.basename(__file__) + ' reads in a sbf2stf converted SBF Receiver Status file and make AGC plots'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-d', '--dir', help='Directory of SBF file (defaults to .)', required=False, default='.', type=str)
    parser.add_argument('-f', '--file', help='Filename of Receiver Status file', required=True, type=str)
    parser.add_argument('-g', '--gnss', help='GNSS System Name', required=True, type=str)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    args = parser.parse_args()

    return args.dir, args.file, args.gnss, args.logging


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


def readSTFRxStatus(stfFile: str, logger: logging.Logger) -> pd.DataFrame:
    """
    read in the STF ReceiverStatus_2 file using included header information
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # read in the file with in
    logger.info('{func:s}: reading file {file:s}'.format(file=stfFile, func=cFuncName))
    dfSTF = pd.read_csv(stfFile, sep=',', skiprows=range(1, 2))

    # remove columns CPULoad[%]  UpTime[s]  RxStatus  RxError  Antenna SampleVar  Blanking[%]
    col2Drop = ['CPULoad[%]', 'UpTime[s]', 'RxStatus', 'RxError', 'Antenna', 'SampleVar', 'Blanking[%]']
    dfSTF.drop(columns=col2Drop, inplace=True, axis=1)

    # drop rows without entry for AGC
    idxNaN = pd.isnull(dfSTF).any(1).to_numpy().nonzero()[0]
    logger.info('{func:s}: dropping NaN on indices {idx!s} (#{nbr:d})'.format(idx=idxNaN, nbr=len(idxNaN), func=cFuncName))
    dfSTF.drop(idxNaN, inplace=True, axis=0)

    # convert the GPS time to UTC
    dfSTF['time'] = dfSTF.apply(lambda x: gpstime.UTCFromWT(x['WNc[week]'], x['TOW[s]']), axis=1)

    # find extreme values in FrontEnd column
    dAGC = {}
    dAGC['min'] = dfSTF['AGCGain[dB]'].min()
    dAGC['max'] = dfSTF['AGCGain[dB]'].max()
    dSTF['AGC'] = dAGC

    # add info to dSTF about time
    dTime = {}
    dTime['epochs'] = len(dfSTF['time'].unique().tolist())
    dTime['date'] = dfSTF.time.iloc[0].strftime('%d %b %Y')
    dTime['start'] = dfSTF.time.iloc[0].strftime('%H:%M:%S')
    dTime['end'] = dfSTF.time.iloc[-1].strftime('%H:%M:%S')
    dSTF['Time'] = dTime

    # find out for wihch FrontEnds a AGC value is reported
    dFrontEnd = {}
    # get unique values for FrontEnd
    lstFrontEnds = np.sort(dfSTF['FrontEnd'].unique().tolist())
    # find the corresponding names
    for i, frontEnd in enumerate(lstFrontEnds):
        dFrontEnd[frontEnd] = {}
        dFrontEnd[frontEnd]['name'] = ssnst.dFrontEnd[frontEnd]
    dSTF['frontend'] = dFrontEnd

    # add info to dSTF about #epochs
    dSTF['#rows'] = dfSTF.shape[0]

    logger.info('{func:s}: read STF file {file:s}, added UTM coordiantes and GNSS time'.format(file=stfFile, func=cFuncName))

    return dfSTF


def main(argv):
    """
    creates a combined SBF file from hourly or six-hourly SBF files
    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    dirSTF, fileSTF, GNSSsyst, logLevels = treatCmdOpts(argv)

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

    # read in the STF file using included header information
    dfAGC = readSTFRxStatus(stfFile=fileSTF, logger=logger)
    amutils.logHeadTailDataFrame(df=dfAGC, dfName=dSTF['stf'], callerName=cFuncName, logger=logger)

    # save to cvs file
    dSTF['csv'] = os.path.splitext(dSTF['stf'])[0] + '.csv'
    dfAGC.to_csv(dSTF['csv'])
    logger.info('{func:s}: saved to csv file {csv:s}'.format(csv=dSTF['csv'], func=cFuncName))

    logger.info('{func:s}: information:\n{dict!s}'.format(dict=dSTF, func=cFuncName))

    # plot the AGC values
    plotagc.plotAGC(dStf=dSTF, dfAgc=dfAGC, logger=logger)
    # plotcoords.plotUTMCoords(dStf=dSTF, dfCrd=dfAGC[['time', 'UTM.E', 'UTM.N', 'Height[m]', 'NrSV', 'SignalInfo', 'dist', '2D/3D']], logger=logger)
    # # plot trajectory
    # plotcoords.plotUTMScatter(dStf=dSTF, dfCrd=dfAGC[['time', 'UTM.E', 'UTM.N', 'SignalInfo', '2D/3D']], logger=logger)

    logger.info('{func:s}: information:\n{dict!s}'.format(dict=dSTF, func=cFuncName))


if __name__ == "__main__":
    main(sys.argv)
