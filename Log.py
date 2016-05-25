from collections import deque
import csv
import time


class CsvOuput:
    def __init__(self):
        name = time.strftime("%H:%M:%S")
        outputfilename = "output/%s_out.csv" % name
        print("Preparing to output %s data to %s" % (name, outputfilename))
        self.outputfile = open(outputfilename, "w")
        self.outputWriter = csv.writer(self.outputfile)
        self.linesInitialized = False
        self.order = self.order2 = []

    def initializelines(self, columns, percent):
        self.order = [k for k in columns]
        self.order2 = [k for k in percent]
        self.outputWriter.writerow(["t"] + [k for k in columns] + [k for k in percent])
        self.linesInitialized = True

    def write(self, time, columns, percent):
        # We need the first timestamp to initialize the lines at the right X value,
        # so do that check first.
        if not self.linesInitialized:
            self.initializelines(columns, percent)
        line = []
        for k in self.order:
            line.append(columns[k])

        for k in self.order2:
            line.append(percent[k])

        outputrow = [time] + line
        self.outputWriter.writerow(outputrow)

    def close(self):
        self.outputfile.close()
