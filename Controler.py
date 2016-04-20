#!/usr/bin/python

import Agent
import threading
import Output
import time
from Order import Order
import random

stop = False


class Looper(threading.Thread):
    total_flex = 0
    total_x = 0
    total_x_max = 0
    total_conso = 0
    total_order = 0
    mode0 = 0
    mode1 = 0
    mode2 = 0
    mode3 = 0

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not stop:
            time.sleep(0.01)
            lock.acquire()
            Looper.total_flex = 0
            Looper.total_x = 0
            Looper.total_x_max = 0
            Looper.total_conso = 0
            Looper.mode0 = 0
            Looper.mode1 = 0
            Looper.mode2 = 0
            Looper.mode3 = 0
            for a in Agent.Agent.agentList:
                a.run()
                Looper.total_flex += a.flex
                Looper.total_x += a.x
                Looper.total_x_max += a.x_max
                Looper.total_conso += a.conso
                Looper.mode0 += a.mode == 0
                Looper.mode1 += a.mode == 1
                Looper.mode2 += a.mode == 2
                Looper.mode3 += a.mode == 3
            lock.release()


class Controler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mystop = False

    def run(self):
        while True:
            time.sleep(5)
            command = input("commande : ").split()
            if len(command) > 0:
                if command[0] == "order":
                    start = time.time() + float(command[2])
                    end = start + float(command[3])
                    order = Order(float(command[1]), start, end, time.time())
                    lock.acquire(1)
                    Agent.send_order(order)
                    lock.release()


lock = threading.Lock()
nbAgents = 100
b_flex = 100
for i in range(0, nbAgents):
    Agent.Agent(b_flex)
plot = Output.PlotOutput((nbAgents + 1) * b_flex)
looper = Looper()
looper.start()
prompt = Controler()
prompt.start()
coef = 100 * nbAgents
counter = 0
while not stop:
    time.sleep(0.5)
    lock.acquire(1)
    graph = {"flex": Looper.total_flex, "x": Looper.total_x, "x_max": Looper.total_x_max,
             "test": random.choice(Agent.Agent.agentList).infos[Agent.AGG].result(), "conso": Looper.total_conso * 0.25}
    percent = {"mode 0": Looper.mode0 * coef, "mode 1": Looper.mode1 * coef, "mode 2": Looper.mode2 * coef,
               "mode 3": Looper.mode3 * coef}
    plot.write(counter, graph, percent)
    lock.release()
    counter += 1
