
class Agregate:
    def __init__(self, t, s, d, w=0):
        self.type = t
        self.val = s
        self.weight = w
        self.date = d
        self.maj = None

    def result(self):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            if self.weight == 0:
                return None
            return self.val / self.weight
        if self.type == AgType.MAX or self.type == AgType.MIN or self.type == AgType.COM:
            return self.val

    # update with a list of values
    def update(self, inbox, t=None):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            self.val = 0
            self.weight = 0
            size = len(inbox)

            for i in range(size):
                a = inbox.pop(0)
                if a.date == t - 1:
                    self.val += a.val
                    self.weight += a.weight
                else:
                    if a.date != t:
                        print(a.date, t)
                    else:
                        inbox.append(a)
            if self.maj is not None:
                self.val += self.maj
                self.maj = None
        if self.type == AgType.MAX:
            while inbox:
                a = inbox.pop()
                if self.date < a.date:
                    self.date = a.date
                if self.date == a.date:
                    if self.val < a.val:
                        self.val = a.val
            if self.maj is not None:
                self.val = self.maj
                self.maj = None
        if self.type == AgType.MIN:
            while inbox:
                a = inbox.pop()
                if self.date < a.date:
                    self.date = a.date
                if self.date == a.date:
                    if self.val > a.val:
                        self.val = a.val
            if self.maj is not None:
                self.val = self.maj
                self.maj = None
        if self.type == AgType.COM:
            while inbox:
                a = inbox.pop()
                if self.date < a.date:
                    self.date = a.date
                if self.date == a.date:
                    self.val = a.val

    def self_update(self, value, date=None, weight=None):
        self.maj = value
        if date is not None:
            self.date = date

    def reset(self, date):
        self.date = date

    def message(self, j):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            return Agregate(self.type, self.val / (j + 1), self.date, self.weight / (j + 1))
        else:
            return Agregate(self.type, self.val, self.date, self.weight)


class AgType:
    SUM = 0
    AVG = 1
    MAX = 2
    MIN = 3
    CNT = 4
    COM = 5
