#!/usr/bin/python

import os
import random
import sys
import time

import matplotlib.pyplot as plt
import numpy

import Agent as Ag
from Aggregate import AgType
from Aggregate import Agregate
from Order import Order


def progress_bar(value, endvalue, run, it, event):
    bar_length = 20
    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write(
        "\rRound {0}: [{1}] {2}({3}%) - event {4}".format(run, arrow + spaces, it, int(round(percent * 100)), event))
    sys.stdout.flush()


legend = ["flex", "x", "x_max", "conso", "fail"]  # "fail", "ratio", "test"] #  , "mode 0", "mode 1", "mode 2"]
# "flex", "x", "x_max", "conso", "fail",
nb_data = len(legend)

nb_agents = 24
b_flex = [100]#, 200, 400, 500, 2000, 3000]
mean_flex = sum(b_flex) / len(b_flex)
probs = [0,0.5] # numpy.random.exponential(0.14, nb_agents)

nb_runs = 1
nb_events = 40
capacity = mean_flex * nb_agents * 0.4  # shedding capacity order (50% total flex)
dur_prep = 10  # nb ite before first event
dur_delay = 10  # nb ite between message and start
dur_shed = 10  # nb ite shedding
dur_recover = 5  # nb ite before next event
nb_ite = dur_prep + (dur_delay + dur_shed + dur_recover) * nb_events


tab = numpy.empty((nb_runs, nb_ite, nb_data))
detail = numpy.empty((nb_ite, nb_agents))
detail2 = numpy.empty((nb_ite, nb_agents))
time_stat = numpy.empty((nb_ite, 2))
perf = numpy.empty((nb_events, 1))
tab_means = numpy.empty((nb_ite, nb_runs))


dur_total_event = dur_delay + dur_shed + dur_recover
print(nb_agents, " agents with ", mean_flex, " avg flexibility.")
print(nb_events, "events of ", dur_shed, " with ", dur_delay, " delay and ", dur_recover, " recover.")
print("Shedding capacity ordered : ", capacity)
print("Starting for ", nb_runs, " x ", nb_ite, " iterations.")

event_cnt = 0

for j in range(nb_runs):
    # tab[j][0] = legend
    Ag.clear()
    for i in range(nb_agents):
        # Ag.Agent(b_flex[i%6], min(probs[i], 1), round(nb_agents/2))
        Ag.Agent(b_flex[i % len(b_flex)], probs[i%len(probs)], round(nb_agents / 3))
    event_cnt = 0
    cumul_x = 0
    for i in range(nb_ite):
        if (i - dur_prep) % dur_total_event == 0:
            start = i + dur_delay
            end = start + dur_shed
            order = Order(capacity, start, end, i)
            Ag.send({Ag.ORDER: Agregate(AgType.COM, order, order.t)})
            cumul_x = 0

        total_flex = total_flex_w = total_x = total_x_max = 0
        total_conso = total_order = mode0 = mode1 = mode2 = mode3 = fail = 0
        sum_time = []
        for a in Ag.Agent.agentList:
            sum_time.append(a.run(i))
            fail += a.fail
            total_flex += a.flex
            total_flex_w += a.flex * - numpy.log(a.fail_prob)
            total_x += a.x
            total_x_max += a.x_max
            total_conso += a.conso
            detail[i][a.id] = a.data["flex"].weight
        cumul_x += fail

        if (i - dur_prep + dur_delay) % dur_total_event <= dur_shed:
            tab_means[i][j] = max(capacity - total_x, 0)
            if total_x < 0:
                print(total_x)
        else:
            tab_means[i][j] = 0

        if (i - dur_prep + dur_delay + dur_shed) % dur_total_event == 0:
            perf[event_cnt] = cumul_x
            event_cnt += 1

        progress_bar(i, nb_ite, j, i, event_cnt)
        # time_stat[i] = [sum([sum_time[i][j] for i in range(0, len(sum_time))]) / nb_agents for j in
        #                 range(0, len(sum_time[0]))]
        tab[j][i] = [total_flex, total_x, total_x_max, total_conso, fail]
        # averages["dev"] if a.averages is not None else 0
        # detail[i] = [a.note for a in Agent.Agent.agentList]
        # a = Agent.Agent.agentList[0]
        # detail2[i] = [a.averages["dev"] if a.averages is not None else 0 for a in Agent.Agent.agentList]

# total_flex, total_x, total_x_max, total_conso, fail,

custom_file_name = "SOA"
dir_name = "np_out/"
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
name = dir_name + custom_file_name + time.strftime("%m-%d_%H:%M_") + str(nb_agents) + "_" + str(nb_runs) + "_" + str(
    nb_events) + "_" + str(
    dur_total_event)
numpy.save(str(name + ".npy"), tab)


plt.figure(1)
plt.title("")
plt.subplot(211)
plt.plot(tab[0], label=legend)
plt.legend(legend)
plt.subplot(212)
# plt.plot(tab_means, label=[i for i in range(nb_runs)])
plt.plot(numpy.mean(tab_means, axis=1), label=nb_runs)
# plt.legend([i for i in range(nb_runs)]+["avg"])
# plt.plot(detail)
# plt.subplot(313)
# plt.plot(detail2)
plt.show()
