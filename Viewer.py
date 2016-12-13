#!/usr/bin/python

import numpy
import matplotlib.pyplot as plt

filename = ""
legend = ["flex", "x", "x_max", "conso", "mode1"]
tab = numpy.load(filename)
plt.figure(1)
plt.plot(tab[0], label=legend)
plt.legend(legend)
plt.show()