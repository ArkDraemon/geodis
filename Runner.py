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


def progressBar(value, endvalue, run, it, event):
    bar_length = 20
    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write(
        "\rRound {0}: [{1}] {2}({3}%) - event {4}".format(run, arrow + spaces, it, int(round(percent * 100)), event))
    sys.stdout.flush()


custom_file_name = "SOA"
nb_agents = 20
b_flex = [100]  # [100, 200,    400, 500, 2000, 3000]
mean_flex = sum(b_flex) / len(b_flex)
probs = numpy.random.exponential(0.14, nb_agents)

plot_on = False
# plot_on = True
nb_runs = 1
nb_events = 120
capacity = mean_flex * nb_agents * 0.3  # shedding capacity order (50% total flex)
dur_prep = 10  # nb ite before first event
dur_delay = 20  # nb ite between message and start
dur_shed = 20  # nb ite shedding
dur_recover = 20  # nb ite before next event
nb_ite = dur_prep + (dur_delay + dur_shed + dur_recover) * nb_events

legend = ["flex", "x", "x_max", "conso"]  # "fail", "ratio", "test"] #  , "mode 0", "mode 1", "mode 2"]
nb_data = len(legend)

F = 0
for i in range(0, nb_agents):
    f = random.choice(b_flex)
    Agent.Agent(f, min(probs[i], 1, round(nb_agents / 2)))
    F += f
if plot_on:
    plot = Output.PlotOutput(F + 1000, False)  # Log.CsvOuput()  #
coef = 100 * nb_agents

tab = numpy.empty((nb_runs, nb_ite, nb_data))
detail = numpy.empty((nb_ite, nb_agents))
detail2 = numpy.empty((nb_ite, nb_agents))
time_stat = numpy.empty((nb_ite, 2))
perf = numpy.empty((nb_events, 1))

dur_total_event = dur_delay + dur_shed + dur_recover
print(nb_agents, " agents with ", mean_flex, " avg flexibility.")
print(nb_events, "events of ", dur_shed, " with ", dur_delay, " delay and ", dur_recover, " recover.")
print("Shedding capacity ordered : ", capacity)
print("Starting for ", nb_runs, " x ", nb_ite, " iterations.")

event_cnt = 0

for j in range(nb_runs):
    # tab[j][0] = legend
    cumul_x = 0
    for i in range(nb_ite):
        # print(i)
        if (i - dur_prep) % dur_total_event == 0:
            start = i + dur_delay
            end = start + dur_shed
            order = Order(capacity, start, end, i)
            Agent.send({"order": Agregate(AgType.COM, order, order.t)})
            cumul_x = 0

        total_flex = total_flex_w = total_x = total_x_max = total_conso = total_order = mode0 = mode1 = mode2 = mode3 = fail = 0
        sum_time = []
        for a in Agent.Agent.agentList:
            sum_time.append(a.run(i))
            fail += a.fail
            total_flex += a.flex
            total_flex_w += a.flex * - numpy.log(a.fail_prob)
            total_x += a.x
            total_x_max += a.x_max
            total_conso += a.conso
            mode0 += a.mode == 0
            mode1 += a.mode == 1
            mode2 += a.mode == 2
            mode3 += a.mode == 3
            if a.mode == 2:
                cumul_x += a.x

        if (i - dur_prep + dur_delay + dur_shed) % dur_total_event == 0:
            perf[event_cnt] = cumul_x * 100 / (capacity * dur_shed)
            event_cnt += 1

        progressBar(i, nb_ite, j, i, event_cnt)
        time_stat[i] = [sum([sum_time[i][j] for i in range(0, len(sum_time))]) / nb_agents for j in
                        range(0, len(sum_time[0]))]
        if plot_on:
            graph = {"flex": total_flex, "x": total_x, "x_max": total_x_max,
                     "conso": total_conso * 0.25, "fail": fail, "ratio": fail / total_flex,
                     "test": random.choice(Agent.Agent.agentList).data["flex"].result()}
            percent = {"mode 0": mode0 * coef, "mode 1": mode1 * coef, "mode 2": mode2 * coef}
            plot.write(i, graph, percent)

        detail[i] = [a.note for a in Agent.Agent.agentList]
        detail2[i] = [a.data["note_max"].result() for a in Agent.Agent.agentList]
        tab[j][i] = [total_flex, total_x, total_x_max, total_conso]
        # tab[j][i] = [((1000 - total_x) / (2000 - total_flex) if total_flex != 2000 else 0), ((1000 - total_x) / (2000 - total_flex_w) if total_flex_w != 2000 else 0), total_x_max, total_conso]

        # , fail, fail / total_flex, random.choice(Agent.Agent.agentList).data[ "flex"].result()]  # , mode0 * coef, mode1 * coef, mode2 * coef]

dir_name = "np_out/"
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
name = dir_name + custom_file_name + time.strftime("%m-%d_%H:%M_") + str(nb_agents) + "_" + str(nb_runs) + "_" + str(
    nb_events) + "_" + str(
    dur_total_event)
numpy.save(str(name + ".npy"), tab)
# numpy.save(str(name + "_out.npy"), time_stat)
plt.figure(1)
plt.title("")
plt.subplot(311)
plt.plot(tab[0], label=legend)
plt.legend(legend)
plt.subplot(312)
plt.plot(perf)
plt.subplot(313)
plt.plot(detail)
# plt.axis([0, len(tab[0]), 0, mean_flex * nb_agents * 1.1])

# plt.subplot(312)
# plt.plot([time_stat[i][0] for i in range(0, len(time_stat))])
# plt.subplot(313)
# plt.plot([time_stat[i][1] for i in range(0, len(time_stat))])
plt.show()
if plot_on:
    plot.close()
