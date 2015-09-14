from pulp.pulp import lpSum, LpProblem, LpVariable
from pulp.constants import LpMaximize, LpStatusOptimal, LpStatusInfeasible,\
    LpStatusUnbounded, LpStatusUndefined, LpStatusNotSolved
from vote.society import Lottery
from itertools import chain, combinations


def createLpSum(choiceClass, choiceNames, choiceVariables):
    return lpSum(choiceVariables[choiceNames[choice]] for choice in choiceClass)


def checkPulpStatus(status,
                    errorInfeasible=True, errorUnbounded=True,
                    errorUndefined=True, errorNotSolved=True):
    if status == LpStatusOptimal:
        return status
    if status == LpStatusInfeasible:
        if errorInfeasible:
            raise ValueError("Infeasible")
        return status
    if status == LpStatusUnbounded:
        if errorUnbounded:
            raise ValueError("Unbounded")
        return status
    if status == LpStatusUndefined:
        if errorUndefined:
            raise ValueError("Undefined")
        return status
    if status == LpStatusNotSolved:
        if errorNotSolved:
            raise ValueError("Not solver")
        return status
    raise ValueError("Unknown status " + repr(status))


def getAllSubsets(elements, startSize=1):
    if startSize == len(elements):
        return set([elements])
    elif startSize > len(elements):
        return set()
    return chain.from_iterable(combinations(elements, i)
                               for i in range(startSize, len(elements)))


def getUniqueNames(objects, prefix="U_"):
    name = 0
    uniqueNames = dict()
    for obj in objects:
        uniqueNames[obj] = prefix + str(name)
        name += 1
    return uniqueNames


def findLottery(vote, classHeights, solverSettings):
    classNames = getUniqueNames(classHeights.keys(), prefix="Class ")
    choiceNames = getUniqueNames(vote.getChoices(), prefix="Choice ")

    problem = LpProblem("Lambda", LpMaximize)
    choiceVariables = LpVariable.dicts("p", choiceNames.values(), lowBound=0)

    problem += lpSum(choiceVariables) <= 1, "Distribution"
    for choiceClass, height in classHeights.items():
        problem += createLpSum(choiceClass, choiceNames, choiceVariables) >= \
            height, classNames[choiceClass] + " height"

    problem.setObjective(lpSum(choiceVariables.values()))
    problem.solve(solverSettings.getSolver())

    choiceValues = dict()
    for choice, choiceName in choiceNames.items():
        choiceValues[choice.getObject()] = choiceVariables[choiceName].value()
    return Lottery(choiceValues, solverSettings)
