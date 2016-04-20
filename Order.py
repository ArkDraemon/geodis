class Order:
    def __init__(self, capacity, start, end, time):
        self.Q = capacity
        self.td = start
        self.tf = end
        self.t = time
