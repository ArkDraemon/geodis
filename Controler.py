#!/usr/bin/python

import Agent
from Agregate import Agregate
from Agregate import AgType
import threading
import Output
import time
from Order import Order
import Log
import random
import numpy

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
    fail = 0

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        counter = 0
        while not stop:
            time.sleep(0.001)
            lock.acquire()
            Looper.total_flex = 0
            Looper.total_x = 0
            Looper.total_x_max = 0
            Looper.total_conso = 0
            Looper.mode0 = 0
            Looper.mode1 = 0
            Looper.mode2 = 0
            Looper.mode3 = 0
            Looper.fail = 0
            for a in Agent.Agent.agentList:
                a.run(time.time())
                Looper.fail += a.fail
                Looper.total_flex += a.flex
                Looper.total_x += a.x
                Looper.total_x_max += a.x_max
                Looper.total_conso += a.conso
                Looper.mode0 += a.mode == 0
                Looper.mode1 += a.mode == 1
                Looper.mode2 += a.mode == 2
                Looper.mode3 += a.mode == 3
            lock.release()
            counter += 1


class Controler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mystop = False

    def run(self):
        global stop
        while not stop:
            time.sleep(5)
            command = input("commande : ").split()
            if len(command) > 0:
                if command[0] == "order":
                    start = float(time.time()) + float(command[2])
                    end = start + float(command[3])
                    order = Order(float(command[1]), start, end, time.time())
                    lock.acquire(1)
                    Agent.send({"order": Agregate(AgType.COM, order)})
                    lock.release()
                if command[0] == "go":
                    for i in range(60):
                        print("top ", i)
                        start = float(time.time()) + float(command[2])
                        end = start + float(command[3])
                        order = Order(float(command[1]), start, end, time.time())
                        lock.acquire(1)
                        Agent.send({"ORDER": Agregate(AgType.COM, order)})
                        lock.release()
                        time.sleep(float(command[2]) + float(command[3]) + 3)
                    stop = True
                if command[0] == "stop":
                    stop = True


lock = threading.Lock()
nbAgents = 200
b_flex = [1000] #[100, 200, 400, 500, 2000, 3000]
probs = numpy.random.exponential(0.14, nbAgents)
F = 0
for i in range(0, nbAgents):
    f = random.choice(b_flex)
    Agent.Agent(f, min(probs[i], 1))
    F += f
plot = Output.PlotOutput(F + 1000) #  Log.CsvOuput()  #
looper = Looper()
looper.start()
prompt = Controler()
prompt.start()
coef = 100 * nbAgents
counter = 0
it_max = 200
tab = numpy.empty((it_max,6))
for i in range(it_max):
    time.sleep(0.5)
    lock.acquire(1)
    graph = {"flex": Looper.total_flex, "x": Looper.total_x, "x_max": Looper.total_x_max,
             "conso": Looper.total_conso * 0.25, "fail": Looper.fail, "ratio": Looper.fail / looper.total_flex, "test": random.choice(Agent.Agent.agentList).data["flex"].result()}
    # tab[i] = []
    percent = {"mode 0": Looper.mode0 * coef, "mode 1": Looper.mode1 * coef, "mode 2": Looper.mode2 * coef,
               "mode 3": Looper.mode3 * coef}
    plot.write(counter, graph, percent)
    lock.release()
    counter += 1
numpy.save("test.npy", tab)
looper.join(1)
print("stop")
plot.close()
