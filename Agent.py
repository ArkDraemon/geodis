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
        self.data[MAX_FIAB] = Agregate(AgType.MAX, 0, 0)
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
        self.coefs = {F: 0.5, C: 0.4, T: 0.1}
        self.hist = {F: [], C: [], T: []}
        self.connect = 10
        self.fail_prob = prob
        self.fail = False
        Agent.agentList.append(self)
        Agent.lastId += 1

    def run(self, t):
        if self.order is not None and abs((self.data[AGG].result() / self.order.Q) - 1) >= 0.0:  # if crossed
            if t - self.cnt >= Agent.t_wait:  # filtre passe-bas
                # print(self.order.Q, " ", self.infos[AGG].result())
                self.x += (self.order.Q - self.data[AGG].result()) * self.x / self.data[AGG].result()  # MAJ
                self.cnt = t
        else:
            self.cnt = t
        if self.x >= self.x_max:
            self.x_max += (self.flex - self.x_max) * 0.5
        self.x_max = min(self.x_max, self.flex)
        self.x = min(self.x, self.x_max)
        if self.mode == 3:
            if t - self.cnt2 >= Agent.t_wait:
                self.eval[C] = self.m_cap * HIST_SIZE / self.data[MAX_CAP].result()
                self.eval[F] = self.m_fiab * HIST_SIZE / self.data[MAX_FIAB].result()
                self.note = self.coefs[F] * self.eval[F] + self.coefs[C] * self.eval[C] + self.coefs[T] * self.eval[
                    T]
                self.infos[NOTE_MAX] = self.note
                self.mode = 0
            else:
                self.cnt2 = t
        if self.mode == 2:
            self.stats["x"] += self.x
            self.stats["ecart"] += self.data[AGG].result()
            self.stats["counter"] += 1
            self.conso = self.base_conso - self.x
            ti = t - self.order.td
            l = self.order.tf - self.order.td
            if not self.fail:
                r = random.random()
                g = 6 * self.fail_prob * ti * ti / (l * (l + 1) * (2 * l + 1))
                self.fail = r < g
                if self.fail:
                    self.flex *= 0.5
            if self.order.tf <= t:  # Fin effacement
                self.order = None
                self.evaluate()
                self.mode = 3
                self.conso = self.base_conso
                self.flex = self.base_flex
                self.cnt2 = t
        if self.mode == 1 and self.order.td <= t:
            # Départ effacement
            self.obj = self.x
            self.stats["x"] = self.x
            self.stats["ecart"] = math.pow(self.order.Q - self.data[AGG].result(), 2)
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
        f = math.sqrt(self.stats["ecart"] / self.stats["counter"])
        t = (1 if self.x_max / self.flex > 0.9 else 0) if self.flex > 0 else 1
        self.hist[F].append(f)
        self.hist[C].append(c)
        self.hist[T].append(t)
        self.eval[T] += t - self.hist[T].pop(0) if len(self.hist[T]) > HIST_SIZE else 0
        if len(self.hist[C]) > HIST_SIZE:
            self.hist[C].pop(0)
        if len(self.hist[F]) > HIST_SIZE:
            self.hist[F].pop(0)
        self.m_cap = sum(self.hist[C]) / float(len(self.hist[C]))
        self.infos[MAX_CAP] = self.m_cap
        self.m_fiab = sum(self.hist[F]) / float(len(self.hist[F]))
        self.infos[MAX_FIAB] = self.m_fiab

    def receive_order(self, o):
        if self.order is None or self.order.t < o.t:
            self.order = o
            send_order(o, self.connect)
            self.x_max = self.note * self.flex / self.data[NOTE_MAX].result()
            self.x = self.x_max
            self.mode = 1
            self.fail = False


def send(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive(m)


def send_order(m, j=1):
    for a in random.sample(Agent.agentList, j):
        a.receive_order(m)
