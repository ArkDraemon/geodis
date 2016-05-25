import numpy
import Agent
from Order import Order

nbAgents = 100
b_flex = 100
Q = 5000
td = 20
tf = 20
probs = numpy.random.exponential(0.5, nbAgents)
M = max(probs)
for i in range(0, nbAgents):
    Agent.Agent(b_flex, probs[i] / M)
stop = False
t = 0
started = False
start = None
end = None
l = dict()
bl = list()
DIFF = "diff"
ECART = "ecart"
k1 = "k1"
k2 = "k2"
k3 = "k3"
counter = 0
while not stop:
    if start is not None and t > start:
        started = True
        l = {DIFF: [], k1: [], k2: [], k3: []}
        start = None
    if started and t >= end:
        started = False
        s = ""
        for k in l:
            s += k + " : " + str(round(sum(l[k])/len(l[k]), 3)) + " "
        print(counter, " - ", s)
        counter += 1
    tmp = {DIFF: [], ECART: [], k1: [], k2: [], k3: []}
    for a in Agent.Agent.agentList:
        a.run(t)
        if started:
            tmp[DIFF].append(a.x)
            tmp[k1].append(a.coefs["f"])
            tmp[k2].append(a.coefs["c"])
            tmp[k3].append(a.coefs["t"])
    if started:
        l[DIFF].append(abs(sum(tmp[DIFF])-Q))
        #l[ECART].append(pow(sum(tmp[DIFF])-Q, 2))
        l[k1].append(sum(tmp[k1])/len(tmp[k1]))
        l[k2].append(sum(tmp[k2]) / len(tmp[k2]))
        l[k3].append(sum(tmp[k3]) / len(tmp[k3]))
    if t > 10 and t % 100 == 0:
        start = t + td
        end = start + tf
        order = Order(float(Q), start, end, t)
        Agent.send_order(order)
    t += 1

