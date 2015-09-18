'''
Created on 9 Sep 2015

@author: Tobias Meggendorfer
'''
import numpy
from pulp.solvers import LpSolver


class SolverSettings(object):

    def __init__(self, solver, absoluteTolerance=10 ** -5, relativeTolerance=10 ** -5):
        self.setAbsoluteTolerance(absoluteTolerance)
        self.setRelativeTolerance(relativeTolerance)
        self.setSolver(solver)

    def setSolver(self, solver):
        if not isinstance(solver, LpSolver):
            raise ValueError(repr(solver) + " is not a LpSolver")
        self.solver = solver

    def getSolver(self):
        return self.solver

    def setAbsoluteTolerance(self, tolerance):
        if tolerance <= 0:
            raise ValueError("Tolerance must be positive")
        self.absoluteTolerance = tolerance

    def setRelativeTolerance(self, tolerance):
        if tolerance <= 0:
            raise ValueError("Tolerance must be positive")
        self.relativeTolerance = tolerance

    def getRelativeTolerance(self):
        return self.relativeTolerance

    def getAbsoluteTolerance(self):
        return self.absoluteTolerance

    def isNonnegative(self, a):
        if a > 0:
            return True
        return self.isClose(a, 0)

    def nonnegativeFuzzyRound(self, a):
        if a > 0:
            return a
        if self.isClose(a, 0):
            return 0
        raise ValueError("Negative value")

    def isClose(self, a, b):
        return numpy.isclose(a, b, self.getRelativeTolerance(), self.getAbsoluteTolerance())

    def isInInterval(self, value, a, b):
        if a > b:
            raise ValueError("a must be smaller than b")
        if value < a:
            return self.isClose(value, a)
        if b < value:
            return self.isClose(b, value)
        return True

    def checkBound(self, value, a, b):
        if self.isInInterval(value, a, b):
            return self.bound(value, a, b)
        raise ValueError("Value " + repr(value) +
                         " out of bounds [" + a + "," + b + "]")

    def bound(self, value, a, b):
        if a > b:
            raise ValueError("a must be smaller than b")
        if value < a:
            return a
        if b < value:
            return b
        return value
