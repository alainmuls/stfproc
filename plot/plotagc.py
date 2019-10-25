import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import dates
from matplotlib import colors as mpcolors
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


def plotAGC(dStf: dict, dfAgc: pd.DataFrame, logger=logging.Logger):
    """
    plots the UTM coordinates and #SVs on 4 different plots as a function of time
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: start plotting AGC values'.format(func=cFuncName))

    amutils.logHeadTailDataFrame(df=dfAgc, dfName='dfAgc', callerName=cFuncName, logger=logger)

    # specify the style
    mpl.style.use('seaborn')
    colors = ['tab:green', 'tab:olive', 'tab:orange', 'tab:cyan', 'tab:blue', 'tab:red', 'tab:pink', 'tab:purple', 'tab:brown', 'tab:white']
    # (re)set the color iterator
    # colorsIter = iter(list(mcolors.TABLEAU_COLORS))
    colorsIter = iter(list(colors))

    fig, ax = plt.subplots(nrows=1, ncols=1, sharex=True)
    fig.set_size_inches(14, 10)

    # for setting the time on time-scale
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfAgc['time'].iloc[0], endDT=dfAgc['time'].iloc[-1])

    # x-axis properties
    ax.set_xlim([dfAgc['time'].iloc[0], dfAgc['time'].iloc[-1]])
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

    # get the index for the different frontends
    dIdx = {}  # dict with indices
    for i, fe in enumerate(dStf['frontend']):
        logger.info('{func:s}: ... plotting frontend[{nr:d}], SSNID = {ssnid:d}, name = {name:s}'.format(nr=i, ssnid=fe, name=dStf['frontend'][fe]['name'], func=cFuncName))

        idx = dfAgc.index[dfAgc['FrontEnd'] == fe]
        logger.info('{func:s}:    ... indices found {idx!s} (#{len:d})'.format(idx=idx, len=len(idx), func=cFuncName))

        # plot the AGC for this frontend
        ax.plot(dfAgc['time'].loc[idx], dfAgc['AGCGain[dB]'].loc[idx], color=next(colorsIter), linestyle='', marker='.', label=dStf['frontend'][fe]['name'], markersize=3)

    # name y-axis
    ax.set_ylabel('AGC Gain [dB]', fontsize=14)

    # add a legend the plot showing 2D/3D positioning displayed
    ax.legend(loc='best', ncol=16, markerscale=6)

    # title of plot
    title = '{syst:s}: AGC Gain [dB]'.format(syst=dStf['gnss'])
    fig.suptitle(title, fontsize=16)

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # Save the file in dir png
    pltDir = os.path.join(dStf['dir'], 'png')
    os.makedirs(pltDir, exist_ok=True)
    pltName = '{syst:s}-AGC.png'.format(syst=dStf['gnss'].replace(' ', '-'))
    pltName = os.path.join(pltDir, pltName)
    fig.savefig(pltName, dpi=100)

    logger.info('{func:s}: plot saved as {name:s}'.format(name=pltName, func=cFuncName))

    plt.show(block=True)
