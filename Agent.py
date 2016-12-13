import random
from Aggregate import Agregate
from Aggregate import AgType
import math
import time
from copy import deepcopy

ORDER = "order"
SUM_PART = "flex"
MAX_CAP = "max_cap"
NOTE_MAX = "note_max"
MAX_FLEX = "max_flex"
MAX_DEV = "max_deviation"
F = "f"
C = "c"
T = "t"
CF = "k1"
CC = "k2"
HIST_SIZE = 10
SUM_DEV = "sum_dev"
SUM_GLOB_DEV = "sum_global_deviation"
COUNTER = "counter"


class Agent:
    lastId = 0
    agentList = []
    t_wait = 3

    def __init__(self, base_flex, prob):
        self.id = Agent.lastId
        self.base_flex = base_flex
        self.flex = self.base_flex  # random.randrange(100)
        self.x_max = self.flex
        self.x = self.x_max
        self.old_x = self.x
        self.note = round(random.random(), 1)
        self.data = dict()
        self.data[SUM_PART] = Agregate(AgType.SUM, self.x, 0, 1 if self.id == 0 else 0)
        self.data[MAX_FLEX] = Agregate(AgType.SUM, self.flex, 0, 1 if self.id == 0 else 0)
        self.data[MAX_CAP] = Agregate(AgType.MAX, self.x, 0)
        self.data[NOTE_MAX] = Agregate(AgType.MAX, self.note, 0)
        self.data[MAX_DEV] = Agregate(AgType.MAX, 0, 0)
        self.inbox = [deepcopy(self.data)]  # envoi à soi-même des valeurs
        self.order = None
        self.cnt = self.mode = 0
        self.stats = dict()
        self.base_conso = base_flex
        self.conso = self.base_conso
        self.coefs = {F: 0.6, C: 0.3, T: 0.1}
        self.hist = []
        self.connect = 10
        self.fail_prob = prob
        self.fail = 0
        self.obj = 0
        self.consensus_reached = None
        self.starting_point = None
        self.failing_point = None
        Agent.agentList.append(self)
        Agent.lastId += 1

    def run(self, t):
        start_time = time.time()
        time_table = []
        if self.order is None and ORDER in self.data and self.data[ORDER].result().td > t:
            self.order = o = self.data[ORDER].result()  # load order
            send({ORDER: self.data[ORDER]}, self.connect)  # propagate order
            self.x_max = self.note * self.flex / self.data[NOTE_MAX].result()  # define virtual limit
            self.x = self.x_max  # set participation tout max possible
            self.mode = 1  # set shedding preparation on
            self.fail = False  # agent has not failed yet
            self.starting_point = self.data[SUM_PART].result()  # record starting time
            self.data[NOTE_MAX].reset(0, self.order.tf)
            if random.random() < self.fail_prob:  # check if must fail
                if self.base_flex < 1000:  # if mode "light"
                    self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0 / 3.0))
                else:  # if mode "heater"
                    self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)
                    # self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0 / 3.0))
                    # self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)
        if self.order is not None:  # if shedding going on (or preparing)
            if abs((self.data[SUM_PART].result() / self.order.Q) - 1) >= 1:  # if crossed
                if t - self.cnt >= Agent.t_wait:  # filtre passe-bas
                    self.x += (self.order.Q - self.data[SUM_PART].result()) * self.x / self.data[
                        SUM_PART].result()  # MAJ
                    self.cnt = t  # initialize low-pass
                    # maybe set consensus_reached = None
            else:
                self.cnt = t  # not crossed, low-pass stays initialized
                if self.consensus_reached is None:  # if consensus was not yet reached
                    self.consensus_reached = t  # set consensus as reached at t
        if self.x >= self.x_max:  # if more flexibility is needed
            self.x_max += (self.flex - self.x_max) * 0.5  # update virtual limit
        self.x_max = min(self.x_max, self.flex)  # limit virtual limit by total flex
        self.x = min(self.x, self.x_max)  # limit engaged flex by virtual limit
        if self.mode == 2:  # during event
            if self.order.tf <= t:  # Fin effacement
                self.evaluate()
                self.order = None
                self.mode = 0
                self.conso = self.base_conso
                self.flex = self.base_flex
                self.x_max = self.base_flex
                self.x = self.x_max
                self.fail = 0
            else:  # during event
                self.stats[SUM_PART] += self.x
                self.stats[SUM_DEV] += math.pow(self.obj - self.x, 2)
                self.stats[SUM_GLOB_DEV] += self.order.Q - self.data[SUM_PART].result()
                self.stats[COUNTER] += 1
                self.conso = self.base_conso - self.x  # update consumption
                if self.failing_point is not None and t >= self.failing_point:  # if must fail now
                    self.flex = 0  # set flexibility to 0
                    self.failing_point = None
                    self.fail = self.x
        if self.mode == 1 and self.order.td <= t:  # Départ effacement
            self.obj = self.x
            self.stats[SUM_PART] = self.x
            self.stats[SUM_DEV] = math.pow(self.obj - self.x, 2)
            self.stats[SUM_GLOB_DEV] = self.order.Q - self.data[SUM_PART].result()
            self.stats[COUNTER] = 1
            self.starting_point = self.data[SUM_PART].result()
            self.mode = 2
        self.data[SUM_PART].self_update(self.x - self.old_x)
        self.old_x = self.x
        time_table.append(time.time() - start_time)
        self.push_sum()
        time_table.append(time.time() - start_time)
        return time_table

    def push_sum(self):
        box = {}  # for each aggregate, contain a temporally ordered list of values
        for m in self.inbox:  # inbox contain a temporally ordered list of pair {aggregate, value}
            for k, v in m.items():  # browse inbox to fill box
                try:
                    box[k].append(v)
                except KeyError:
                    box[k] = [v]
        self.inbox.clear()  # void inbox for next use
        for k in box:  # update each aggregate with list of new values
            try:
                self.data[k].update(box[k])  # update aggregate
            except KeyError:
                self.data[k] = box[k][0]  # if aggregate is not known, create it
        message = dict()  # prepare propagation message
        # for each aggregate, prepare the value to be sent (divide by neighbours if needed)
        message.update((k, self.data[k].message(self.connect)) for k in self.data)
        send(message, self.connect)  # send propagation message
        self.receive(message)  # send message to self

    def receive(self, m):
        self.inbox.append(deepcopy(m))

    def evaluate(self):
        f = math.sqrt(self.stats[SUM_DEV] / self.stats[COUNTER]) # average squared deviation from first commitment (obj)
        c = self.stats[SUM_PART] / self.stats[COUNTER]
        t = (1 if self.x_max / self.flex > 0.9 else 0) if self.flex > 0 else 1
        # k1 = self.stats[SUM_GLOB_DEV] / self.stats[COUNTER]
        # k2 = (self.consensus_reached - self.order.t) / abs(self.starting_point - self.order.Q)

        self.hist.append({F: f, C: c, T: t, CF: self.coefs[F], CC: self.coefs[C]})  # append latest stats
        if len(self.hist) > HIST_SIZE:  # control history size
            self.hist.pop(0)

        size = len(self.hist)
        averages = {k: float(sum(item[k] for item in self.hist) / size) for k in
                    self.hist[0]}  # calculate average for each parameter
        # [{'f': 3, 'c': 4},{'f': 5, 'c': 2}] = {'f': 8, 'c': 6}

        self.data[MAX_CAP].self_update(averages[C])
        self.data[MAX_DEV].self_update(averages[F])

        reliability = 1 - ((averages[F] / self.data[MAX_DEV].result()) if self.data[MAX_DEV].result() > 0 else 0)
        capacity = averages[C] * size / self.data[MAX_CAP].result()
        turnover = averages[T]

        self.note = self.coefs[F] * reliability + self.coefs[C] * capacity + self.coefs[T] * turnover

        self.data[NOTE_MAX].self_update(self.note)


        # k1 = self.coefs[F]  # /= averages[CF]
        # k2 = self.coefs[C]  # /= averages[CC]
        # k3 = self.coefs[T]
        # s = k1 + k2 + k3
        # self.coefs[F] = k1 / s
        # self.coefs[C] = k2 / s
        # self.coefs[T] = k3 / s


def send(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive(m)
