#!/usr/bin/python

import Agent
from agregate import Agregate
from agregate import AgType
import Output
import time
from Order import Order
import Log
import random
import numpy
import matplotlib.pyplot as plt

nbAgents = 200
b_flex = [1000]  # [100, 200, 400, 500, 2000, 3000]
probs = numpy.random.exponential(0.14, nbAgents)

plot_on = False
# plot_on = True
nb_runs = 1
nb_events = 3
capacity = 100000
dur_prep = 10
dur_delay = 10
dur_shed = 5
dur_recover = 10
nb_ite = dur_prep + (dur_delay + dur_shed + dur_recover) * nb_events

legend = ["flex", "x", "x_max", "conso"]  # , "fail", "ratio", "test"] #  , "mode 0", "mode 1", "mode 2"]
nb_data = len(legend)

F = 0
for i in range(0, nbAgents):
    f = random.choice(b_flex)
    Agent.Agent(f, min(probs[i], 1))
    F += f
if plot_on:
    plot = Output.PlotOutput(F + 1000)  # Log.CsvOuput()  #
coef = 100 * nbAgents

tab = numpy.empty((nb_runs, nb_ite, nb_data))
dur_total_event = dur_delay + dur_shed + dur_recover
time_stat = numpy.empty((nb_ite, 2))
print("starting for ", nb_runs, " x ", nb_ite, " iterations.")
for j in range(nb_runs):
    # tab[j][0] = legend
    for i in range(nb_ite):
        # print(i)
        if (i - dur_prep) % dur_total_event == 0:
            start = i + dur_delay
            end = start + dur_shed
            order = Order(capacity, start, end, i)
            Agent.send({"order": Agregate(AgType.COM, order)})
            #  print("event sent")
        total_flex = total_x = total_x_max = total_conso = total_order = mode0 = mode1 = mode2 = mode3 = fail = 0
        sum_time = []
        for a in Agent.Agent.agentList:
            sum_time.append(a.run(i))
            fail += a.fail
            total_flex += a.flex
            total_x += a.x
            total_x_max += a.x_max
            total_conso += a.conso
            mode0 += a.mode == 0
            mode1 += a.mode == 1
            mode2 += a.mode == 2
            mode3 += a.mode == 3
        print("iteration ", i)
        time_stat[i] = [sum([sum_time[i][j] for i in range(0, len(sum_time))]) / nbAgents for j in
                        range(0, len(sum_time[0]))]
        if plot_on:
            graph = {"flex": total_flex, "x": total_x, "x_max": total_x_max,
                     "conso": total_conso * 0.25, "fail": fail, "ratio": fail / total_flex,
                     "test": random.choice(Agent.Agent.agentList).data["flex"].result()}
            percent = {"mode 0": mode0 * coef, "mode 1": mode1 * coef, "mode 2": mode2 * coef}
            plot.write(i, graph, percent)

        tab[j][i] = [total_flex, total_x, total_x_max, total_conso]
        # , fail, fail / total_flex, random.choice(Agent.Agent.agentList).data[ "flex"].result()]  # , mode0 * coef, mode1 * coef, mode2 * coef]

dir_name = "np_out/"
name = dir_name + time.strftime("%m-%d_%H:%M_") + str(nbAgents) + "_" + str(nb_runs) + "_" + str(
    nb_events) + "_" + str(
    dur_total_event)
numpy.save(str(name + ".npy"), tab)
#numpy.save(str(name + "_out.npy"), time_stat)
plt.figure(1)
plt.subplot(311)
plt.plot(tab[0], label=legend)
plt.legend(legend)
plt.axis([0, len(tab[0]), -5000, 500000])
# plt.subplot(312)
# plt.plot([time_stat[i][0] for i in range(0, len(time_stat))])
# plt.subplot(313)
# plt.plot([time_stat[i][1] for i in range(0, len(time_stat))])
plt.show()
print("stop")
if plot_on:
    plot.close()
