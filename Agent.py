import random
from Aggregate import Agregate
from Aggregate import AgType
from copy import deepcopy

ORDER = "order"
SUM_X = "flex"
MAX_CAP = "max_capacity"
MIN_CAP = "min_capacity"
MAX_DEV = "max_deviation"
MIN_DEV = "min_deviation"
DEV = "deviation"
C = "c"
SUM_DEV = "sum_dev"
SUM_GLOB_DEV = "sum_global_deviation"
CNT = "counter"
TAU = 0.1
H = 0.01
T_WAIT = 10
ADJ_T = 0.5
P = 1

def clear():
    Agent.lastId = 0
    Agent.agentList.clear()


class Agent:
    lastId = 0
    agentList = []

    def __init__(self, base_flex, prob, connect=10):
        self.id = Agent.lastId
        self.base_flex = base_flex
        self.flex = self.base_flex
        self.x = 0
        self.old_x = self.x
        self.reliability = 0.5
        self.data = dict()
        self.data[SUM_X] = Agregate(AgType.SUM, self.x, -1, 1 if self.id == 0 else 0)
        self.data[MAX_DEV] = Agregate(AgType.MAX, 0, 0)
        self.data[MIN_DEV] = Agregate(AgType.MIN, 0, 0)
        self.data[MAX_CAP] = Agregate(AgType.MAX, self.base_flex, 0)
        self.data[MIN_CAP] = Agregate(AgType.MIN, self.base_flex, 0)
        self.inbox = [deepcopy(self.data)]  # envoi à soi-même des valeurs
        self.order = None
        self.cnt = 0
        self.mode = 0
        self.stats = dict()
        self.base_conso = base_flex + 100
        self.conso = self.base_conso
        self.connect = connect
        self.fail_prob = prob
        self.fail = 0
        self.obj = 0
        self.failing_point = None
        self.mean_dev = None
        self.reaction_t = None
        self.adj_t = None

        Agent.agentList.append(self)
        Agent.lastId += 1

    def run(self, t):
        agg = self.data[SUM_X].result()
        # Receiving order
        if self.order is None and ORDER in self.data and self.data[ORDER].result().td > t:
            self.order = o = self.data[ORDER].result()  # load order
            send({ORDER: self.data[ORDER]}, self.connect)  # propagate order
            self.evaluate()
            delta = (o.td - t) * ADJ_T
            self.adj_t = t + delta
            self.reaction_t = t + delta * (1 - self.reliability)
            self.mode = 1  # set shedding preparation on
            self.fail = 0  # agent has not failed yet
            if random.random() < self.fail_prob or (t > 1600 and self.reliability > 0.99):  # check if must fail
                if self.base_flex < 1000:  # if mode "light"
                    self.failing_point = o.td + (o.tf - o.td) * 0.7 * (1 - pow(random.random(), 1.0 / 3.0))
                else:  # if mode "heater"
                    self.failing_point = o.td + (o.tf - o.td) * 0.7 * pow(random.random(), 1.0 / 3.0)
                #self.failing_point = o.td + (o.tf - o.td) * 0.5

        if self.mode == 3:  # during event
            if self.order.tf <= t:  # Fin effacement
                self.pre_evaluate()
                self.order = None
                self.mode = 0
                self.conso = self.base_conso
                self.flex = self.base_flex
                self.fail = 0
                self.x = 0
            else:  # during event
                self.stats[SUM_DEV] += (self.obj - self.x)**2
                self.stats[SUM_GLOB_DEV] += self.obj**2
                self.stats[CNT] += 1
                self.conso = self.base_conso - self.x  # update consumption
                if self.failing_point is not None and t >= self.failing_point:  # if must fail now
                    self.flex = 0  # set flexibility to 0
                    self.failing_point = None
                    self.fail = self.x
                    self.x = 0

        if self.mode == 2 and self.order.td <= t:  # Départ effacement
            self.obj = self.x  # set objective for deviation evaluation
            self.stats[SUM_DEV] = 0  # reset
            self.stats[SUM_GLOB_DEV] = 0
            self.stats[CNT] = 0
            self.conso = self.base_conso - self.x
            self.mode = 3

        if self.mode == 1 and self.reaction_t <= t:
            diff = self.order.Q - agg
            c_max = self.data[MAX_CAP].result()
            c_min = self.data[MIN_CAP].result()
            c = c_min * (c_max - self.base_flex) / (c_max - c_min) * P
            engage = self.reliability * (self.base_flex * P - c) + c
            self.x = min(engage, diff) if diff > 0 else self.reliability
            self.mode = 2
            self.cnt = t

        # if shedding going on (or preparing)
        if self.mode > 1 and t > self.adj_t:
            if agg > 0 and abs(self.order.Q - agg) / self.order.Q >= H:  # if crossed
                if t - self.cnt >= T_WAIT:  # low-pass filter
                    self.x += self.x * (self.order.Q - agg) / agg  # MAJ
                    self.cnt = t  # initialize low-pass
            else:
                self.cnt = t  # not crossed, low-pass stays initialized
        self.x = min(self.x, self.flex)  # limit engaged flex by total flex

        self.data[SUM_X].self_update(self.x - self.old_x, t)  # update aggregate on total participation

        if self.fail == 0:  # if not failing, update objective to match regular ajustment
            self.obj += self.x - self.old_x
        self.old_x = self.x  # update memo
        self.push_sum(t)
        return True

    def pre_evaluate(self):
        deviation = self.stats[SUM_DEV]/self.stats[SUM_GLOB_DEV] if self.stats[SUM_GLOB_DEV] > 0 else 0.5
        if self.mean_dev is None: # first event
            self.mean_dev = deviation
        else:
            self.mean_dev = self.mean_dev * (1 - TAU) + TAU * deviation
        self.data[MAX_DEV].self_update(self.mean_dev, self.order.tf)
        self.data[MIN_DEV].self_update(self.mean_dev, self.order.tf)
        self.data[MAX_CAP].self_update(self.base_flex, self.order.tf)
        self.data[MIN_CAP].self_update(self.base_flex, self.order.tf)

    def evaluate(self):
        if self.mean_dev is not None:
            max_d = self.data[MAX_DEV].result()
            min_d = self.data[MIN_DEV].result()
            if max_d != min_d:
                self.reliability = (self.mean_dev - max_d) / (min_d - max_d)


    def push_sum(self, t):
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
                self.data[k].update(box[k], t)  # update aggregate
                for v in box[k]:
                    self.inbox.append({k : v})
            except KeyError:
                self.data[k] = box[k][0]  # if aggregate is not known, create it
        message = dict()  # prepare propagation message
        # for each aggregate, prepare the value to be sent (divide by neighbours if needed)
        message.update((k, self.data[k].message(self.connect)) for k in self.data)
        send(message, self.connect, self)  # send propagation message
        self.receive(message)  # send message to self

    def receive(self, m):
        self.inbox.append(deepcopy(m))


def send(m, j=1, exclude=None):
    sample = random.sample(Agent.agentList, j)
    while exclude in sample:
        sample = random.sample(Agent.agentList, j)
    for a in sample:
        a.receive(m)
