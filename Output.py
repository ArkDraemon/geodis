# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
Provides two classes with the same signature for writing data out of NuPIC
models.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
from collections import deque
from abc import ABCMeta, abstractmethod
# Try to import matplotlib, but we don't have to.
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
matplotlib.use('tkagg')

WINDOW = 100


class PlotOutput:
    def __init__(self, ylim):
        # Turn matplotlib interactive mode on.
        plt.ion()
        self.date = []
        self.actualValues = {}
        self.actualPercent = {}
        self.actualLines = {}
        self.percentlines = {}
        self.linesInitialized = False
        self.graph = []
        fig = plt.figure()
        gs = gridspec.GridSpec(2, 1)
        self.graph = fig.add_subplot(gs[0, 0])
        plt.title("Geodis")
        plt.grid(True)
        plt.ylabel("kW")
        plt.gca().set_ylim([0, ylim])
        self.monitor = fig.add_subplot(gs[1, 0])
        plt.gca().set_ylim([-2, 102])
        plt.ylabel("%")
        plt.xlabel("steps")
        plt.tight_layout()

    def initializelines(self, columns, percent):
        self.date = deque([0], maxlen=WINDOW)
        plt.legend([k for k in columns])
        for k in columns:
            self.actualValues[k] = deque([0.0], maxlen=WINDOW)
            self.actualLines[k], = self.graph.plot(self.date, self.actualValues[k], label=k)
        for k in percent:
            self.actualPercent[k] = deque([0.0], maxlen=WINDOW)
            self.percentlines[k], = self.monitor.plot(self.date, self.actualPercent[k], label=k)
        self.graph.legend(handles=[v for k, v in self.actualLines.items()], loc=3)
        self.monitor.legend(handles=[v for k, v in self.percentlines.items()], loc=3)
        self.linesInitialized = True

    def write(self, time, columns, percent):
        # We need the first timestamp to initialize the lines at the right X value,
        # so do that check first.
        if not self.linesInitialized:
            self.initializelines(columns, percent)

        self.date.append(time)
        for k, v in self.actualValues.items():
            v.append(columns[k])
            # Update data
            self.actualLines[k].set_xdata(self.date)
            self.actualLines[k].set_ydata(v)

        self.graph.relim()
        self.graph.autoscale_view(True, True, True)

        for k, v in self.actualPercent.items():
            v.append(percent[k])
            # Update data
            self.percentlines[k].set_xdata(self.date)
            self.percentlines[k].set_ydata(v)

        self.monitor.relim()
        self.monitor.autoscale_view(True, True, True)
        #plt.xlim(xmin=0)
        plt.show()
        plt.pause(0.001)

    def close(self):
        plt.ioff()
        plt.show()
