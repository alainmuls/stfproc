import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import dates
import numpy as np
import pandas as pd
import matplotlib.colors as mcolors

import sys
import os
from pandas.plotting import register_matplotlib_converters
import logging
from termcolor import colored

from plot import plot_utils
from ampyutils import amutils

register_matplotlib_converters()


def plotUTMCoords(dStf: dict, dfCrd: pd.DataFrame, logger=logging.Logger):
    """
    plots the UTM coordinates and #SVs on 4 different plots as a function of time
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    crds = ['UTM.E', 'UTM.N', 'Height[m]', 'dist', 'NrSV']
    # crds = ['dist', 'NrSV']

    logger.info('{func:s}: start plotting UTM coordinates'.format(func=cFuncName))

    amutils.logHeadTailDataFrame(df=dfCrd, dfName='dfCrd', callerName=cFuncName, logger=logger)

    # specify the style
    mpl.style.use('seaborn')

    fig, axes = plt.subplots(nrows=len(crds), ncols=1, sharex=True)
    fig.set_size_inches(18.5, 15)

    # get the index for 2D/3D
    idx3D = dfCrd.index[dfCrd['2D/3D'] == 0]
    idx2D = dfCrd.index[dfCrd['2D/3D'] == 1]

    # get the index for signals used for PNT AND for 3D/2D
    dIdx = {}  # dict with indices corresponding to signals & 3D/2D usage
    for st, lstSTNames in dStf['signals'].items():
        stNames = ",".join(lstSTNames)
        logger.info('{func:s}: st = {st:d}  name = {name!s}'.format(st=st, name=stNames, func=cFuncName))
        dIdx[st] = {}
        dIdx[st]['3D'] = dfCrd.index[(dfCrd['SignalInfo'] == st) & (dfCrd['2D/3D'] == 0)]
        dIdx[st]['2D'] = dfCrd.index[(dfCrd['SignalInfo'] == st) & (dfCrd['2D/3D'] == 1)]
        logger.info('{func:s}: list of indices dIdx[{st:d}][3D] = {idx!s}'.format(st=st, idx=dIdx[st]['3D'], func=cFuncName))
        logger.info('{func:s}: list of indices dIdx[{st:d}][2D] = {idx!s}'.format(st=st, idx=dIdx[st]['2D'], func=cFuncName))

    # for setting the time on time-scale
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfCrd['time'].iloc[0], endDT=dfCrd['time'].iloc[-1])

    for crd, ax in zip(crds, axes):
        # print in order UTM.E, UTM.N, height, and NrSV and indicate 2D/3D by alpha
        logger.info('{func:s}: plotting {crd:s}'.format(crd=crd, func=cFuncName))

        # x-axis properties
        ax.set_xlim([dfCrd['time'].iloc[0], dfCrd['time'].iloc[-1]])
        if dtFormat['minutes']:
            ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45], interval=1))
        else:
            ax.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
        ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

        ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
        ax.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

        ax.xaxis.set_tick_params(rotation=0)
        for tick in ax.xaxis.get_major_ticks():
            # tick.tick1line.set_markersize(0)
            # tick.tick2line.set_markersize(0)
            tick.label1.set_horizontalalignment('center')

        # (re)set the color iterator
        colorsIter = iter(list(mcolors.TABLEAU_COLORS))

        if crd is not 'NrSV':
            # plot according to signals used and 2D/3D
            for st, lstSTNames in dStf['signals'].items():
                stNames = ",".join(lstSTNames)
                for mode in '3D', '2D':
                    lblTxt = '{st:s} ({mode:s})'.format(st=stNames, mode=mode)
                    logger.debug('{func:s}: plotting {stm:s}'.format(stm=lblTxt, func=cFuncName))

                    # get the index for this sigType & mode
                    idx = dIdx[st][mode]
                    ax.plot(dfCrd['time'].iloc[idx], dfCrd[crd].iloc[idx], color=next(colorsIter), linestyle='', marker='.', label=lblTxt, markersize=2)
        else:
            # plot when 3D posn
            ax.fill_between(dfCrd['time'], dfCrd[crd], color='grey', alpha=.2)

            # plot when 3D posn
            ax.plot(dfCrd['time'].iloc[idx3D], dfCrd[crd].iloc[idx3D], color='green', linestyle='', marker='.', markersize=2, label='3D')
            # plot when 2D posn
            ax.plot(dfCrd['time'].iloc[idx2D], dfCrd[crd].iloc[idx2D], color='red', linestyle='', marker='.', markersize=2, label='2D')

        # name y-axis
        ax.set_ylabel(crd, fontsize=14)

        # add a legend the plot showing 2D/3D positioning displayed
        ax.legend(loc='best', ncol=16, markerscale=5)

    # title of plot
    title = '{syst:s}: UTM Coordinates'.format(syst=dStf['gnss'])
    fig.suptitle(title, fontsize=16)

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # Save the file in dir png
    pltDir = os.path.join(dStf['dir'], 'png')
    os.makedirs(pltDir, exist_ok=True)
    pltName = '{syst:s}-UTM.png'.format(syst=dStf['gnss'].replace(' ', '-'))
    pltName = os.path.join(pltDir, pltName)
    fig.savefig(pltName, dpi=100)

    logger.info('{func:s}: plot saved as {name:s}'.format(name=pltName, func=cFuncName))

    plt.show(block=False)


def plotUTMScatter(dStf: dict, dfCrd: pd.DataFrame, logger=logging.Logger):
    """
    plots the UTM E-N scatter
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: start plotting trajectories'.format(func=cFuncName))

    # specify the style
    mpl.style.use('seaborn')

    # get the index for signals used for PNT AND for 3D/2D
    dIdx = {}  # dict with indices corresponding to signals & 3D/2D usage
    for st, lstSTNames in dStf['signals'].items():
        stNames = ",".join(lstSTNames)
        logger.info('{func:s}: st = {st:d}  name = {name:s}'.format(st=st, name=stNames, func=cFuncName))
        dIdx[st] = {}
        dIdx[st]['3D'] = dfCrd.index[(dfCrd['SignalInfo'] == st) & (dfCrd['2D/3D'] == 0)]
        dIdx[st]['2D'] = dfCrd.index[(dfCrd['SignalInfo'] == st) & (dfCrd['2D/3D'] == 1)]
        logger.info('{func:s}: list of indices dIdx[{st:d}][3D] = {idx!s}'.format(st=st, idx=dIdx[st]['3D'], func=cFuncName))
        logger.info('{func:s}: list of indices dIdx[{st:d}][2D] = {idx!s}'.format(st=st, idx=dIdx[st]['2D'], func=cFuncName))

    # convert time column to seconds
    dsTime = dfCrd['time']-dfCrd['time'].iloc[0]
    dfCrd['sec'] = dsTime.dt.total_seconds()
    amutils.logHeadTailDataFrame(df=dfCrd, dfName='dfCrd plot scatter', callerName=cFuncName, logger=logger)

    # get index when sec is multiple of 10 minutes
    idxTime = dfCrd.index[dfCrd['sec'] % 600 == 0]
    logger.debug('{func:s}: indices multiple of 300s = {idx!s}'.format(idx=idxTime, func=cFuncName))

    fig, ax = plt.subplots(nrows=1, ncols=1)
    fig.set_size_inches(14, 14)
    ax.axis('equal')

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # get the index for 2D/3D
    idx3D = dfCrd.index[dfCrd['2D/3D'] == 0]
    idx2D = dfCrd.index[dfCrd['2D/3D'] == 1]

    # (re)set the color iterator
    colorsIter = iter(list(mcolors.TABLEAU_COLORS))

    # plot the E-N coordinates according to signals used and 2D/3D mode
    for st, lstSTNames in dStf['signals'].items():
        stNames = ",".join(lstSTNames)
        for mode in '3D', '2D':
            lblTxt = '{st:s} ({mode:s})'.format(st=stNames, mode=mode)
            logger.debug('{func:s}: plotting {stm:s}'.format(stm=lblTxt, func=cFuncName))

            # get the index for this sigType & mode
            idx = dIdx[st][mode]
            ax.plot(dfCrd['UTM.E'].iloc[idx], dfCrd['UTM.N'].iloc[idx], color=next(colorsIter), linestyle='', marker='.', label=lblTxt, markersize=2)


    # ax.plot(dfCrd['UTM.E'].iloc[idx3D], dfCrd['UTM.N'].iloc[idx3D], color='blue', label='3D mode', markersize=2, linestyle='', marker='.')
    # ax.plot(dfCrd['UTM.E'].iloc[idx2D], dfCrd['UTM.N'].iloc[idx2D], color='red', label='2D mode', markersize=2, linestyle='', marker='.')

    # annotate plot with time
    annText = [dfCrd['time'][idx].strftime('%H:%M:%S') for idx in idxTime]
    logger.info('{func:s}: annotate text\n{ann!s}'.format(ann=annText, func=cFuncName))
    for idx, text in zip(idxTime, annText):
        ax.annotate(text, (dfCrd['UTM.E'].iloc[idx], dfCrd['UTM.N'].iloc[idx]), textcoords='offset points', xytext=(0,10), ha='center')

    # annotate with position of marker
    logger.info('{func:s}: marker location = {E!s} {N!s}'.format(E=dStf['marker']['UTM.E'], N=dStf['marker']['UTM.N'], func=cFuncName))
    E, N = dStf['marker']['UTM.E'], dStf['marker']['UTM.N']
    ax.annotate('marker', xy=(E,N), xytext=(E-200,N), xycoords='data', horizontalalignment='right', verticalalignment='center', color='magenta')
    ax.scatter(E, N, color='magenta', marker='^')

    # draw circles for distancd evaluation on plot
    for radius in range(5, 50, 5):
        newCircle = plt.Circle((E,N), radius*1000, color='red', fill=False, clip_on=True, alpha=0.4)
        ax.add_artist(newCircle)
        # annotate the radius
        ax.annotate('{radius:d} km'.format(radius=radius), xy=(E+radius*1000*np.cos(np.pi*5/4), N+radius*1000*np.sin(np.pi*5/4)), textcoords='data', xycoords='data', clip_on=True, color='blue', alpha=0.4)
    for radius in 2.5, 7.5:
        newCircle = plt.Circle((E,N), radius*1000, color='red', fill=False, clip_on=True, alpha=0.4)
        ax.add_artist(newCircle)
        # annotate the radius
        ax.annotate('{radius:.1f} km'.format(radius=radius), xy=(E+radius*1000*np.cos(np.pi*5/4), N+radius*1000*np.sin(np.pi*5/4)), textcoords='data', xycoords='data', clip_on=True, color='blue', alpha=0.4)

    # name y-axis
    ax.set_xlabel('UTM.E', fontsize=14)
    ax.set_ylabel('UTM.N', fontsize=14)

    # add a legend the plot showing 2D/3D positioning displayed
    ax.legend(loc='best', ncol=16, markerscale=5)

    # title of plot
    title = '{syst:s}: UTM Trajectory'.format(syst=dStf['gnss'])
    fig.suptitle(title, fontsize=16)

    # Save the file in dir png
    pltDir = os.path.join(dStf['dir'], 'png')
    os.makedirs(pltDir, exist_ok=True)
    pltName = '{syst:s}-UTMscatter.png'.format(syst=dStf['gnss'].replace(' ', '-'))
    pltName = os.path.join(pltDir, pltName)
    fig.savefig(pltName, dpi=100)
    logger.info('{func:s}: plot saved as {name:s}'.format(name=pltName, func=cFuncName))

    plt.show(block=True)


def plotUTMSuppressed(dStf: dict, dfCrd: pd.DataFrame, logger=logging.Logger):
    """
    plots the UTM E-N scatter

    PVT error code. The following values are defined:
    0: no error.
    1: not enough measurements
    2: not enough ephemerides available
    3: DOP too large (larger than 15)
    4: sum of squared residuals too large
    5: no convergence
    6: not enough measurements after outlier rejection
    7: position output prohibited due to export laws
    8: not enough differential corrections available
    9: base station coordinates unavailable
    127: valid position output actively suppressed (e.g. PRS denial)
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: start plotting (un)suppressed trajectories'.format(func=cFuncName))

    # specify the style
    mpl.style.use('seaborn')

    # get the index for PVT suppression
    dIdx = {}  # dict with indices corresponding to PNT suppression
    for errCode in dStf['errCodes']:
        dIdx[errCode] = dfCrd.index[dfCrd['Error'] == errCode]
        logger.info('{func:s}: list of indices dIdx[{errc:d}] = {idx!s}'.format(errc=errCode, idx=dIdx[errCode], func=cFuncName))

    # convert time column to seconds
    dsTime = dfCrd['time']-dfCrd['time'].iloc[0]
    dfCrd['sec'] = dsTime.dt.total_seconds()
    amutils.logHeadTailDataFrame(df=dfCrd, dfName='dfCrd plot scatter', callerName=cFuncName, logger=logger)

    # get index when sec is multiple of 10 minutes
    idxTime = dfCrd.index[dfCrd['sec'] % 300 == 0]
    logger.debug('{func:s}: indices multiple of 300s = {idx!s}'.format(idx=idxTime, func=cFuncName))

    fig, ax = plt.subplots(nrows=1, ncols=1)
    fig.set_size_inches(14, 14)
    ax.axis('equal')

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # (re)set the color iterator
    colorsIter = iter(list(mcolors.TABLEAU_COLORS))

    # plot the E-N coordinates according to PVT Error mode
    for errCode, errCodeName in dStf['errCodes'].items():
        logger.debug('{func:s}: plotting {errc:d}: {errtxt:s}'.format(errc=errCode, errtxt=errCodeName, func=cFuncName))

        # get the index for this error code
        idx = dIdx[errCode]
        ax.plot(dfCrd['UTM.E'].iloc[idx], dfCrd['UTM.N'].iloc[idx], color=next(colorsIter), linestyle='', marker='.', label=errCodeName, markersize=4)

    # ax.plot(dfCrd['UTM.E'].iloc[idx3D], dfCrd['UTM.N'].iloc[idx3D], color='blue', label='3D mode', markersize=2, linestyle='', marker='.')
    # ax.plot(dfCrd['UTM.E'].iloc[idx2D], dfCrd['UTM.N'].iloc[idx2D], color='red', label='2D mode', markersize=2, linestyle='', marker='.')

    # annotate plot with time
    annText = [dfCrd['time'][idx].strftime('%H:%M:%S') for idx in idxTime]
    logger.info('{func:s}: annotate text\n{ann!s}'.format(ann=annText, func=cFuncName))
    for idx, text in zip(idxTime, annText):
        ax.annotate(text, (dfCrd['UTM.E'].iloc[idx], dfCrd['UTM.N'].iloc[idx]), textcoords='offset points', xytext=(0,10), ha='center')

    # draw circles for zones on plot
    for zone, zone_crd in dStf['zones'].items():
        E, N, R = zone_crd['UTM.E'], zone_crd['UTM.N'], zone_crd['radius']

        # draw marker & cricle
        ax.scatter(E, N, color='black', marker='^', alpha=0.4)
        newCircle = plt.Circle((E, N), R, color='black', fill=False, clip_on=True)
        ax.add_artist(newCircle)

        # annotate the markers
        ax.annotate('{zone:s}'.format(zone=zone), xy=(E + 2, N), textcoords='data', xycoords='data', clip_on=True, color='black', alpha=0.4)

    # name y-axis
    ax.set_xlabel('UTM.E', fontsize=14)
    ax.set_ylabel('UTM.N', fontsize=14)

    # add a legend the plot showing 2D/3D positioning displayed
    ax.legend(loc='best', ncol=16, markerscale=5)

    # title of plot
    title = '{syst:s}: UTM Trajectory'.format(syst=dStf['gnss'])
    fig.suptitle(title, fontsize=16)

    # Save the file in dir png
    pltDir = os.path.join(dStf['dir'], 'png')
    os.makedirs(pltDir, exist_ok=True)
    pltName = '{syst:s}-UTMsuppressed.png'.format(syst=dStf['gnss'].replace(' ', '-'))
    pltName = os.path.join(pltDir, pltName)
    fig.savefig(pltName, dpi=100)
    logger.info('{func:s}: plot saved as {name:s}'.format(name=pltName, func=cFuncName))

    plt.show(block=True)
