import numpy
import Agent
from Order import Order

nbAgents = 100
b_flex = 100
probs = numpy.random.exponential(0.3, nbAgents)
M = max(probs)
for i in range(0, nbAgents):
    Agent.Agent(b_flex, 0.0) #probs[i] / M)
stop = False
t = 0
started = False
start = None
end = None
l = list()
bl = list()
while not stop:
    if start is not None and t > start:
        started = True
        start = None
    if started and t >= end:
        started = False
        bl.append(sum(l)/len(l))
        print(sum(l)/len(l))
        l = list()
    tmp = list()
    for a in Agent.Agent.agentList:
        a.run(t)
        if started:
            tmp.append(a.x)
    if started:
        l.append(abs(sum(tmp)-6000))
    if t > 10 and t % 100 == 0:
        start = t + 20
        end = start + 60
        order = Order(float(6000), t + 20, t + 20 + 60, t)
        Agent.send_order(order)
    t += 1

