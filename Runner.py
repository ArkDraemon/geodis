#!/usr/bin/python

import Agent
import os
import sys
from Aggregate import Agregate
from Aggregate import AgType
import Output
import time
from Order import Order
import Log
import random
import numpy
import matplotlib.pyplot as plt


def progressBar(value, endvalue, lap, bar_length=20):
    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write("\rRound {0}: [{1}] {2}%".format(lap, arrow + spaces, int(round(percent * 100))))
    sys.stdout.flush()

custom_file_name = "SOA"
nb_agents = 10
b_flex = [1000]  # [100, 200,    400, 500, 2000, 3000]
mean_flex = sum(b_flex)/len(b_flex)
probs = numpy.random.exponential(0.14, nb_agents)

plot_on = False
# plot_on = True
nb_runs = 1
nb_events = 10
capacity = mean_flex * nb_agents * 0.5 # shedding capacity order (50% total flex)
dur_prep = 10 # nb ite before first event
dur_delay = 10 # nb ite between message and start
dur_shed = 10 # nb ite shedding
dur_recover = 10 # nb ite before next event
nb_ite = dur_prep + (dur_delay + dur_shed + dur_recover) * nb_events

legend = ["flex", "x", "x_max", "conso", "mode1"]  # , "fail", "ratio", "test"] #  , "mode 0", "mode 1", "mode 2"]
nb_data = len(legend)

F = 0
for i in range(0, nb_agents):
    f = random.choice(b_flex)
    Agent.Agent(f, min(probs[i], 1))
    F += f
if plot_on:
    plot = Output.PlotOutput(F + 1000, False)  # Log.CsvOuput()  #
coef = 100 * nb_agents

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
            Agent.send({"order": Agregate(AgType.COM, order, order.t)})
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
        progressBar(i, nb_ite, j)
        time_stat[i] = [sum([sum_time[i][j] for i in range(0, len(sum_time))]) / nb_agents for j in
                        range(0, len(sum_time[0]))]
        if plot_on:
            graph = {"flex": total_flex, "x": total_x, "x_max": total_x_max,
                     "conso": total_conso * 0.25, "fail": fail, "ratio": fail / total_flex,
                     "test": random.choice(Agent.Agent.agentList).data["flex"].result()}
            percent = {"mode 0": mode0 * coef, "mode 1": mode1 * coef, "mode 2": mode2 * coef}
            plot.write(i, graph, percent)

        tab[j][i] = [total_flex, total_x, total_x_max, total_conso, mode1*100]
        # , fail, fail / total_flex, random.choice(Agent.Agent.agentList).data[ "flex"].result()]  # , mode0 * coef, mode1 * coef, mode2 * coef]
dir_name = "np_out/"
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
name = dir_name + custom_file_name + time.strftime("%m-%d_%H:%M_") + str(nb_agents) + "_" + str(nb_runs) + "_" + str(
    nb_events) + "_" + str(
    dur_total_event)
numpy.save(str(name + ".npy"), tab)
#numpy.save(str(name + "_out.npy"), time_stat)
plt.figure(1)
plt.subplot(111)
plt.plot(tab[0], label=legend)
plt.legend(legend)
plt.axis([0, len(tab[0]), -500, mean_flex * nb_agents * 1.1])
# plt.subplot(312)
# plt.plot([time_stat[i][0] for i in range(0, len(time_stat))])
# plt.subplot(313)
# plt.plot([time_stat[i][1] for i in range(0, len(time_stat))])
plt.show()
if plot_on:
    plot.close()

