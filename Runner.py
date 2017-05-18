#!/usr/bin/python

import os
import random
import sys
import time

import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler
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
    str = "Round {0}: [{1}] {2}({3}%) - event {4}\r\r".format(run, arrow + spaces, it, int(round(percent * 100)), event+1)
    print(str, end='\r', flush=True)

seed = 13 # 2 events

seed = 13#13#42#23#32654#145632#568432#5464#1755623

random.seed(seed)
numpy.random.seed(seed)

nb_agents = 18
b_flex = [100, 200, 400, 500, 2000, 3000]
mean_flex = sum(b_flex) / len(b_flex)
probs = numpy.random.exponential(0.14, nb_agents)

title = "no note no delay"
nb_runs = 1
nb_events = 6
capacity = mean_flex * nb_agents * 0.4  # shedding capacity order (50% total flex)
dur_prep = 30  # nb ite before first event
dur_delay = 200  #200# nb ite between message and start
dur_shed = 200  #200# nb ite shedding
dur_recover = 20  # nb ite before next event
dur_total_event = dur_delay + dur_shed + dur_recover
nb_ite = dur_prep + dur_total_event * nb_events
print(nb_ite)

legend = [r'$\sum f_t$', r'$\sum f_e$', "conso.", r'$\hat{F}_e$']#, "fail"]
nb_data = len(legend)
tab = numpy.empty((nb_runs, nb_ite, nb_data))
detail = numpy.empty((nb_ite, nb_agents))
detail2 = numpy.empty((nb_ite, nb_agents))
tab_runs = numpy.empty((nb_ite, nb_runs))
tab_ev_qual = numpy.zeros((nb_events, nb_runs))
tab_fail = numpy.zeros((nb_ite, nb_runs))

print(nb_agents, " agents with ", mean_flex, " avg flexibility.")
print(nb_events, "events of ", dur_shed, " with ", dur_delay, " delay and ", dur_recover, " recover.")
print("Shedding capacity ordered : ", capacity)
print("Starting for ", nb_runs, " x ", nb_ite, " iterations.")

rounds = [6, 5, 10, 15, 18]
cap = 0
for j in range(nb_runs):
    #random.seed(seed)
    Ag.clear()
    connect = 6# rounds[j]#round(nb_agents / (j+1))
    for i in range(nb_agents):
        Ag.Agent(b_flex[i % len(b_flex)], probs[i % len(probs)], connect)
    event_cnt = 0
    start = None
    end = None
    for i in range(nb_ite):
        if (i - dur_prep) % dur_total_event == 0:
            start = i + dur_delay
            end = start + dur_shed
            order = Order(capacity, start, end)
            Ag.send({Ag.ORDER: Agregate(AgType.COM, order, i)}, connect)
        total_flex = total_flex_w = total_x = 0
        total_conso = total_order = mode0 = mode1 = mode2 = mode3 = total_fail = 0
        for a in Ag.Agent.agentList:
            if a.run(i):
                total_fail += a.fail
                total_flex += a.flex
                total_flex_w += a.flex
                total_x += a.x
                total_conso += a.conso
                detail[i][a.id] = a.x
                detail2[i][a.id] = a.data[Ag.SUM_X].result()
        tab_runs[i][j] = total_x
        diff = abs(capacity - total_x) - capacity * Ag.H
        tab_fail[i][j] = 0
        if start is not None and start <= i and i < end:
        #     tab_fail[event_cnt][j] += total_fail
            tab_fail[i][j] = max(diff, 0)
            cap = capacity
            tab_ev_qual[event_cnt][j] += max(diff, 0)
        if end is not None and i >= end:
            start = None
            end = None
            event_cnt += 1
            cap = 0
        progress_bar(i, nb_ite, j, i, event_cnt)
        tab[j][i] = [total_flex, total_x, total_conso, cap]#, total_fail]
        time.sleep(0.1)


custom_file_name = "SOA"
dir_name = "np_out/"
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
name = dir_name + custom_file_name + time.strftime("%m-%d_%H:%M_") + str(nb_agents) + "_" + str(nb_runs) + "_" + str(
    nb_events) + "_" + str(
    dur_total_event)
# numpy.save(str(name + ".npy"), tab)

# nb_col = 1
# nb_line = 1
# mpl.rcParams['lines.linewidth'] = 1.5
# plt.rc('axes', prop_cycle=(cycler('color', ['b', 'g', 'r', 'm']) + cycler('linestyle', ['--', '-', ':', '-.'])))
# plt.figure(1).canvas.set_window_title(title)
# plt.subplot2grid((nb_line, nb_col), (0, 0), colspan=2)
# plt.plot(detail2)
# plt.plot(tab_runs, label=[i for i in range(nb_runs)])
# plt.legend([rounds[i] for i in range(nb_runs)])
# plt.plot(tab[0], label=legend)
# plt.legend(legend)
# plt.subplot2grid((nb_line, nb_col), (1, 0), colspan=2)
# plt.plot(tab_ev_qual, label=[i for i in range(nb_runs)])
# plt.plot(numpy.mean(tab_ev_qual, axis=1), label=nb_runs)
# plt.legend([i for i in range(nb_runs)]+["avg"])
# plt.subplot2grid((nb_line, nb_col), (1, 0), colspan=2)
# plt.plot(tab_fail, label=[i for i in range(nb_runs)])
# plt.plot(numpy.mean(tab_fail, axis=1), label=nb_runs)
# plt.legend([i for i in range(nb_runs)]+["avg"])
# plt.subplot2grid((nb_line, nb_col), (2, 0), colspan=2)
# plt.plot(detail)
# plt.subplot2grid((nb_line, nb_col), (1, 0))
# plt.plot(detail2)
# plt.show()

# plt.figure(1, facecolor='white')
# ax = plt.subplot(111)
#
# ax.plot(tab[0], label=legend)
# box = ax.get_position()
# ax.set_position([box.x0, box.y0 + box.height * 0.05, box.width, box.height * 0.95])
# # plt.title(title)
# ax.legend(legend, loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, ncol=4)
# # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
# # ax.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5))
# plt.show()


## échec normal
#mpl.rcParams['lines.linewidth'] = 1.5
plt.rc('axes', prop_cycle=(cycler('color', ['b', 'g', 'r', 'm']) + cycler('linestyle', ['--', '-', ':', '-.'])))
f = 13
col = nb_runs
plt.figure(1, facecolor='white', figsize=(10,6)).canvas.set_window_title(title)
# for i in range(nb_runs) :
#     ax = plt.subplot(col, 1, i+1)
#     ax.plot(tab[i], label=legend)
#     box = ax.get_position()
#     ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
#     ax.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size':f})
#     ax.set_xlim([0, nb_ite])
ax = plt.subplot(col, 1, col)
ax.plot(tab_fail, '-', label=0, )
box = ax.get_position()
ax.set_position([box.x0*0.6, box.y0, box.width * 0.92, box.height])
ax.legend([r'$|(F_e(t) - \hat{F}_e|$'], loc='center left', bbox_to_anchor=(1, 0.5), prop={'size':f})
ax.set_xlim([0, nb_ite])
ax.set_ylim([0, 3000])
# ax = plt.subplot(212)
# ax.bar(numpy.arange(nb_events), numpy.mean(tab_ev_qual, axis=1), 1, yerr=numpy.std(tab_ev_qual, axis=1), ecolor='r')
# x0, x1, y0, y1 = plt.axis()
# m = 0.9
# plt.axis((x0 - m,
#           x1 + m,
#           y0 - m,
#           y1 + m))
plt.show()

## barres et écart-type
# nb_col = 1
# nb_line = 1
# plt.figure(1, facecolor='white')
# ax = plt.subplot(111)
# ax.bar(numpy.arange(nb_events), numpy.mean(tab_ev_qual, axis=1), 1, yerr=numpy.std(tab_ev_qual, axis=1), ecolor='r')
# print(tab_ev_qual)
# print(numpy.std(tab_ev_qual, axis=1))
#
# plt.show()

## 2 events adjust
# nb_col = 1
# nb_line = 1
# mpl.rcParams['lines.linewidth'] = 1.5
# plt.rc('axes', prop_cycle=(cycler('color', ['b', 'g', 'r', 'm']) + cycler('linestyle', ['--', '-', ':', '-.'])))
# plt.figure(1, facecolor='white')
# ax = plt.subplot(111)
# ax.plot(tab[0], label=legend)
# box = ax.get_position()
# ax.set_position([box.x0, box.y0 + box.height * 0.05, box.width, box.height * 0.95])
# ax.legend(legend, loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, ncol=4)
# plt.show()