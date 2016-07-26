import random
from agregate import Agregate
from agregate import AgType
import math
import time
from copy import deepcopy

ORDER = "order"
AGG = "flex"
MAX_CAP = "max_cap"
NOTE_MAX = "note_max"
MAX_FLEX = "max_flex"
MAX_FIAB = "max_fiab"
F = "f"
C = "c"
T = "t"
CF = "k1"
CC = "k2"
HIST_SIZE = 10


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
        self.note = random.randrange(10)
        self.data = dict()
        self.data[AGG] = Agregate(AgType.SUM, self.x, 1 if self.id == 0 else 0)
        self.data[MAX_FLEX] = Agregate(AgType.SUM, self.flex, 1 if self.id == 0 else 0)
        self.data[MAX_CAP] = Agregate(AgType.MAX, self.x)
        self.data[NOTE_MAX] = Agregate(AgType.MAX, self.note)
        self.data[MAX_FIAB] = Agregate(AgType.MIN, 0)
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
            self.order = o = self.data[ORDER].result()
            send({ORDER: self.data[ORDER]}, self.connect)
            self.x_max = self.note * self.flex / self.data[NOTE_MAX].result()
            self.x = self.x_max
            self.mode = 1
            self.fail = False
            self.starting_point = self.data[AGG].result()
            if random.random() < self.fail_prob:
                if self.base_flex < 1000:
                    self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0 / 3.0))
                else:
                    self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)
                    # self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0 / 3.0))
                    # self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)
        if self.order is not None:
            if abs((self.data[AGG].result() / self.order.Q) - 1) >= 1:  # if crossed
                if t - self.cnt >= Agent.t_wait:  # filtre passe-bas
                    self.x += (self.order.Q - self.data[AGG].result()) * self.x / self.data[AGG].result()  # MAJ
                    self.cnt = t
            else:
                self.cnt = t
                if self.consensus_reached is None:
                    self.consensus_reached = t
        if self.x >= self.x_max:
            self.x_max += (self.flex - self.x_max) * 0.5
        self.x_max = min(self.x_max, self.flex)
        self.x = min(self.x, self.x_max)
        if self.mode == 2:
            if self.order.tf <= t:  # Fin effacement
                self.evaluate()
                self.order = None
                self.mode = 0
                self.conso = self.base_conso
                self.flex = self.base_flex
                self.fail = 0
            else:
                self.stats["x"] += self.x
                self.stats["ecart"] += math.pow(self.obj - self.x, 2)
                self.stats["diff"] += self.order.Q - self.data[AGG].result()
                self.stats["counter"] += 1
                self.conso = self.base_conso - self.x
                if self.failing_point is not None and t >= self.failing_point:
                    self.flex = 0
                    self.failing_point = None
                    self.fail = self.x
        if self.mode == 1 and self.order.td <= t:  # Départ effacement
            self.obj = self.x
            self.stats["x"] = self.x
            self.stats["ecart"] = math.pow(self.obj - self.x, 2)
            self.stats["diff"] = self.order.Q - self.data[AGG].result()
            self.stats["counter"] = 1
            self.starting_point = self.data[AGG].result()
            self.mode = 2
        self.data[AGG].self_update(self.x - self.old_x)
        self.old_x = self.x
        time_table.append(time.time() - start_time)
        self.push_sum()
        time_table.append(time.time() - start_time)
        return time_table

    def push_sum(self):
        box = {}
        for m in self.inbox:
            for k, v in m.items():
                try:
                    box[k].append(v)
                except KeyError:
                    box[k] = [v]
        self.inbox.clear()
        for k in box:
            try:
                self.data[k].update(box[k])
            except KeyError:
                self.data[k] = box[k][0]
        message = dict()
        message.update((k, self.data[k].message(self.connect)) for k in self.data)
        send(message, self.connect)
        self.receive(message)

    def receive(self, m):
        self.inbox.append(deepcopy(m))

    def evaluate(self):
        f = math.sqrt(self.stats["ecart"] / self.stats["counter"])
        c = self.stats["x"] / self.stats["counter"]
        t = (1 if self.x_max / self.flex > 0.9 else 0) if self.flex > 0 else 1
        k1 = self.stats["diff"] / self.stats["counter"]
        k2 = (self.consensus_reached - self.order.t) / abs(self.starting_point - self.order.Q)

        self.hist.append({F: f, C: c, T: t, CF: k1, CC: k2})
        if len(self.hist) > HIST_SIZE:
            self.hist.pop(0)

        size = len(self.hist)
        averages = {k: float(sum(item[k] for item in self.hist) / size) for k in self.hist[0]}
        # [{'f': 3, 'c': 4},{'f': 5, 'c': 2}] = {'f': 8, 'c': 6}

        reliability = self.data[MAX_FIAB].result() * size / (averages[F] if averages[F] != 0.0 else 1)
        capacity = averages[C] * size / self.data[MAX_CAP].result()
        turnover = averages[T]

        self.note = self.coefs[F] * reliability + self.coefs[C] * capacity + self.coefs[T] * turnover

        self.data[MAX_CAP].self_update(averages[C])
        self.data[MAX_FIAB].self_update(averages[F])
        self.data[NOTE_MAX].self_update(self.note)

        k1 = self.coefs[F]  # /= averages[CF]
        k2 = self.coefs[C]  # /= averages[CC]
        k3 = self.coefs[T]
        s = k1 + k2 + k3
        self.coefs[F] = k1 / s
        self.coefs[C] = k2 / s
        self.coefs[T] = k3 / s


def send(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive(m)
