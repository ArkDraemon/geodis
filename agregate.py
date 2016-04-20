import Message


class Agregate:
    def __init__(self, t, s, w=0):
        self.type = t
        self.val = s
        self.weight = w

    def result(self):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            if self.weight == 0:
                return None
            return self.val / self.weight
        if self.type == AgType.MAX or self.type == AgType.MIN:
            return self.val

    def update(self, inbox):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            self.val = 0
            self.weight = 0
            while inbox:
                a = inbox.pop()
                self.val += a.val
                self.weight += a.weight
        if self.type == AgType.MAX:
            while inbox:
                a = inbox.pop()
                if self.val < a.val:
                    self.val = a.val
        if self.type == AgType.MIN:
            while inbox:
                a = inbox.pop()
                if self.val > a.val:
                    self.val = a.val

    def message(self, flag, j=1):
        if self.type == AgType.SUM or self.type == AgType.AVG or self.type == AgType.CNT:
            return Message.Message(Agregate(self.type, self.val / (j + 1), self.weight / (j + 1)), flag)
        if self.type == AgType.MAX or self.type == AgType.MIN:
            return Message.Message(Agregate(self.type, self.val, self.weight), flag)


class AgType:
    SUM = 0
    AVG = 1
    MAX = 2
    MIN = 3
    CNT = 4
