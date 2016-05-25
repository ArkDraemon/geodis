import random
from agregate import Agregate
from agregate import AgType
import math
from copy import deepcopy

AGG = "flex"
MAX_CAP = "max_cap"
MIN_CAP = "min_cap"
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
    t_wait = 1

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
        self.data[MAX_CAP] = Agregate(AgType.MAX, self.x, 0)
        self.data[NOTE_MAX] = Agregate(AgType.MAX, self.note, 0)
        self.data[MAX_FIAB] = Agregate(AgType.MIN, 0, 0)
        self.inbox = {}
        self.infos = {}
        for k, v in self.data.items():
            self.inbox[k] = [deepcopy(v)]  # envoi à soi-même des valeurs
            self.infos[k] = None
        self.order = None
        self.cnt = self.cnt2 = self.mode = self.obj = 0
        self.stats = dict()
        self.base_conso = base_flex
        self.conso = self.base_conso
        self.m_cap = self.x
        self.m_fiab = 0
        self.eval = {F: 0, C: 0, T: 0}
        self.coefs = {F: 0.6, C: 0.3, T: 0.1}
        self.hist = {F: [], C: [], T: [], CF: [], CC: []}
        self.connect = 10
        self.fail_prob = prob
        self.fail = 0
        Agent.agentList.append(self)
        Agent.lastId += 1
        self.consensus_reached = None
        self.starting_point = None
        self.failing_point = None

    def run(self, t):
        if self.order is not None:
            if abs((self.data[AGG].result() / self.order.Q) - 1) >= 0.02:  # if crossed
                if t - self.cnt >= Agent.t_wait:  # filtre passe-bas
                    # print(self.order.Q, " ", self.infos[AGG].result())
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
        if self.mode == 3:
            if t - self.cnt2 >= Agent.t_wait:
                self.eval[C] = self.m_cap * HIST_SIZE / self.data[MAX_CAP].result()
                #self.eval[F] = self.data[MAX_FIAB].result() * HIST_SIZE / self.m_fiab
                #print(self.note)
                self.note = self.coefs[F] * self.eval[F] + self.coefs[C] * self.eval[C] + self.coefs[T] * self.eval[
                    T]
                self.infos[NOTE_MAX] = self.note
                self.mode = 0
        if self.mode == 2:
            if self.starting_point is None:
                self.starting_point = self.data[AGG].result()
            self.stats["x"] += self.x
            self.stats["ecart"] += math.pow(self.obj - self.x, 2)
            self.stats["diff"] += self.order.Q - self.data[AGG].result()
            self.stats["counter"] += 1
            self.conso = self.base_conso - self.x
            if self.failing_point is not None and t >= self.failing_point:
                self.flex = 0
                self.failing_point = None
                self.fail = self.x
            if self.order.tf <= t:  # Fin effacement
                self.evaluate()
                self.order = None
                self.mode = 3
                self.conso = self.base_conso
                self.flex = self.base_flex
                self.cnt2 = t
                self.fail = 0
        if self.mode == 1 and self.order.td <= t:
            # Départ effacement
            self.obj = self.x
            self.stats["x"] = self.x
            self.stats["ecart"] = math.pow(self.obj - self.x, 2)
            self.stats["diff"] = self.order.Q - self.data[AGG].result()
            self.stats["counter"] = 1
            self.mode = 2
        self.infos[AGG] = self.x - self.old_x
        self.old_x = self.x
        self.push_sum()

    def push_sum(self):
        for k, v in self.data.items():
            v.update(self.inbox[k])
            v.self_update(self.infos[k])
            self.propagate(k, v)

    def propagate(self, k, v):
        message = v.message(k, self.connect)
        send(message, self.connect)
        self.receive(message)

    def receive(self, m):
        self.inbox[m.f].append(deepcopy(m.a))

    def evaluate(self):
        c = self.stats["x"] / self.stats["counter"]

        k1 = self.stats["diff"] / self.stats["counter"]
        k2 = self.coefs[C]
        if self.starting_point is not None and self.consensus_reached is not None:
            k2 = (self.consensus_reached - self.order.t) / abs(self.starting_point - self.order.Q)
        t = (1 if self.x_max / self.flex > 0.9 else 0) if self.flex > 0 else 1

        self.hist[C].append(c)
        self.hist[T].append(t)
        self.hist[CF].append(k1)
        self.hist[CC].append(k2)
        self.eval[T] += t - self.hist[T].pop(0) if len(self.hist[T]) > HIST_SIZE else 0

        if len(self.hist[C]) > HIST_SIZE:
            self.hist[C].pop(0)
        if len(self.hist[CF]) > HIST_SIZE:
            self.hist[CF].pop(0)
        if len(self.hist[CC]) > HIST_SIZE:
            self.hist[CC].pop(0)
        self.m_cap = sum(self.hist[C]) / float(len(self.hist[C]))
        f = 0 if self.fail > 0 else 1 #(1 if self.m_cap / self.obj >= 0.7 else 0) if self.obj > 0 else 0  # math.sqrt(self.stats["ecart"] / self.stats["counter"])
        #print(f, " ", self.m_cap / self.obj if self.obj > 0 else 0)
        self.hist[F].append(f)

        self.eval[F] += f - self.hist[F].pop(0) if len(self.hist[F]) > HIST_SIZE else 0
        self.infos[MAX_CAP] = self.m_cap
        self.m_fiab = sum(self.hist[F]) / float(len(self.hist[F]))
        self.infos[MAX_FIAB] = self.m_fiab
        avg_quality = sum(self.hist[CF]) / float(len(self.hist[CF]))
        avg_delay = sum(self.hist[CC]) / float(len(self.hist[CC]))
        k1 = self.coefs[F] #/= avg_quality
        k2 = self.coefs[C] #/= avg_delay
        k3 = self.coefs[T]
        s = k1 + k2 + k3
        self.coefs[F] = k1 / s
        self.coefs[C] = k2 / s
        self.coefs[T] = k3 / s

    def receive_order(self, o):
        if self.order is None or self.order.t < o.t:
            self.order = o
            send_order(o, self.connect)
            self.x_max = self.flex # self.note * self.flex / self.data[NOTE_MAX].result()
            #print(self.x_max, " ", self.note, "  ", self.data[NOTE_MAX].result())
            self.x = self.x_max
            self.mode = 1
            self.fail = False
            self.starting_point = self.data[AGG].result()
            if random.random() < self.fail_prob:
                if self.base_flex < 1000:
                    self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0/3.0))
                else:
                    self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)
                # self.failing_point = o.td + (o.tf - o.td) * (1 - pow(random.random(), 1.0 / 3.0))
                self.failing_point = o.td + (o.tf - o.td) * pow(random.random(), 1.0 / 3.0)


def send(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive(m)


def send_order(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive_order(m)
