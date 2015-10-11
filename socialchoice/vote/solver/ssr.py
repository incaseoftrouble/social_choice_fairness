'''
Created on 10 Sep 2015

@author: Tobias Meggendorfer
'''
from vote.society import ChoiceClass, Agent
from vote.solver.settings import SolverSettings
from itertools import ifilter
from vote.solver.util import getUniqueNames, createLpSum, findLottery,\
    getAllSubsets, checkPulpStatus
from pulp.pulp import LpVariable, LpProblem, lpSum
from pulp.constants import LpMaximize


class Tower(object):

    def __init__(self, choiceClass, name=None):
        if not isinstance(choiceClass, ChoiceClass):
            raise TypeError(repr(choiceClass) + " is not a choice class")
        self.frozen = False
        self.height = 0
        self.choiceClass = choiceClass
        self.name = name
        self.speed = 0

    def getHeight(self):
        return self.height

    def isFrozen(self):
        return self.frozen

    def setHeight(self, height, ignoreFrozen=False):
        if self.isFrozen() and not ignoreFrozen and not self.height == height:
            raise ValueError("Can't change tower height after freeze")
        if height < 0 or 1 < height:
            raise ValueError("Height must be between 0 and 1, " +
                             str(height) + " given")
        if height == 1:
            self.setFrozen()
        self.height = height

    def tryClimb(self, climberHeight):
        if climberHeight > self.height:
            self.setHeight(climberHeight)

    def setFrozen(self):
        self.setSpeed(0)
        self.frozen = True

    def getName(self):
        if self.name is not None:
            return self.name
        return str(self.getChoiceClass())

    def setSpeed(self, speed):
        if speed != 0 and self.isFrozen():
            raise ValueError("Can't change speed after freeze")
        if speed < 0:
            raise ValueError("Speed must be nonnegative")
        self.speed = speed

    def addSpeed(self, speed):
        self.setSpeed(self.getSpeed() + speed)

    def getSpeed(self):
        return self.speed

    def getChoiceClass(self):
        return self.choiceClass

    def __str__(self):
        if self.isFrozen():
            return self.getName() + "@" + str(self.getHeight()) + "(F)"
        return self.getName() + "@" + str(self.getHeight()) + "/" + str(self.getSpeed())

    def __repr__(self):
        return "Tower[" + str(self) + "]"

    def __eq__(self, other):
        if isinstance(other, Tower):
            return self.getChoiceClass() == other.getChoiceClass()
        return False

    def __hash__(self):
        return hash(self.getChoiceClass())


class AgentData(object):
    '''
    This class keeps track of agents' basic data used in SR-like algorithms
    '''

    def __init__(self, agent, speed=1):
        if not isinstance(agent, Agent):
            raise ValueError(repr(agent) + " is not an agent")
        self.agent = agent
        self._choiceClassIter = iter(agent.getChoiceClasses())
        self.currentChoiceClass = next(self._choiceClassIter)

    def getAgent(self):
        return self.agent

    def getCurrentChoiceClass(self):
        return self.currentChoiceClass

    def advanceCurrentChoiceClass(self):
        if self.isFinished():
            return None
        self.currentChoiceClass = next(self._choiceClassIter, None)
        return self.currentChoiceClass

    def isFinished(self):
        return self.currentChoiceClass is None

    def __str__(self):
        if self.isFinished():
            return str(self.getAgent()) + "(F)"
        return str(self.getAgent()) + ":" + str(self.getCurrentChoiceClass())

    def __eq__(self, other):
        if isinstance(other, AgentData):
            return self.getAgent() == other.getAgent()
        return False

    def __hash__(self):
        return hash(self.getAgent())


class SSRState(object):

    def __init__(self, vote, settings):
        if not isinstance(settings, SolverSettings):
            raise TypeError(repr(settings) + " is not a settings instance")
        self.time = 0
        self.settings = settings
        self.vote = vote
        self.towers = dict()
        self.agents = dict()
        for agent in vote.getAgents():
            self.agents[agent] = AgentData(agent)

    def getChoices(self):
        return self.vote.getChoices()

    def getTower(self, choiceClass):
        if not isinstance(choiceClass, ChoiceClass):
            choiceClass = ChoiceClass(choiceClass)
        tower = self.towers.get(choiceClass, None)
        if tower is None:
            tower = Tower(ChoiceClass(choiceClass))
            self.towers[choiceClass] = tower
        return tower

    def getTowers(self):
        '''
        @rtype list(Tower)
        '''
        return self.towers.values()

    def getActiveAgents(self):
        return map(lambda data: data.getAgent(), self._getActiveAgentData())

    def _getActiveAgentData(self):
        return ifilter(lambda data: not data.isFinished(), self.agents.values())

    def adjustTowerSpeeds(self):
        for tower in self.getTowers():
            tower.setSpeed(0)
        for agentData in self._getActiveAgentData():
            currentChoiceClass = agentData.getCurrentChoiceClass()
            self.getTower(currentChoiceClass).addSpeed(1)
            for subset in getAllSubsets(self.vote.getChoices(), len(currentChoiceClass) + 1):
                if currentChoiceClass.isSubsetOf(subset):
                    tower = self.getTower(subset)
                    if not tower.isFrozen():
                        tower.addSpeed(1)

    def isFinished(self):
        for agentData in self.agents.values():
            if not agentData.isFinished():
                return False
        return True

    def advance(self, climbingTime, freezingTowers):
        for tower in self.getTowers():
            if tower.isFrozen():
                continue
            climbedHeight = tower.getHeight() + climbingTime * \
                tower.getSpeed()
            if not self.getSettings().isInInterval(climbedHeight, 0, 1):
                raise ValueError(repr(tower) + " pushed  to height " +
                                 str(climbedHeight))
            climbedHeight = self.settings.bound(climbedHeight, 0, 1)
            tower.setHeight(climbedHeight)
            if tower in freezingTowers:
                tower.setFrozen()
        for agentData in self._getActiveAgentData():
            currentChoiceClass = agentData.getCurrentChoiceClass()
            while currentChoiceClass is not None and self.getTower(currentChoiceClass).isFrozen():
                currentChoiceClass = agentData.advanceCurrentChoiceClass()
        self.adjustTowerSpeeds()

    def getSettings(self):
        return self.settings

    def getNonFrozenTowers(self):
        return ifilter(lambda tower: not tower.isFrozen(), self.towers.values())

    def __str__(self):
        return "Agents: " + ", ".join(map(str, sorted(self.agents.values(),
                                                      key=lambda data: data.getAgent()))) + "\n" + \
            "Towers: " + " ".join(map(str, sorted(self.towers.values(),
                                                  key=lambda tower: tower.getChoiceClass())))


def computeLambda(state, maximumTime=1.0):
    '''
    @type state: SSRState
    @type maximumTime: float
    '''
    towerNames = getUniqueNames(state.getTowers(), prefix="T")
    choiceNames = getUniqueNames(state.getChoices(), prefix="")
    choiceVariables = LpVariable.dicts("p", choiceNames.values(), lowBound=0.0)
    lambdaVariable = LpVariable("l", lowBound=0.0, upBound=maximumTime)

    def createConstraints(problem, variable):
        problem += lpSum(choiceVariables) <= 1, "Distribution"
        for tower, towerName in towerNames.items():
            problem += createLpSum(tower.getChoiceClass(), choiceNames, choiceVariables) >= \
                tower.getHeight() + variable * \
                tower.getSpeed(), towerName

    problem = LpProblem("Lambda", LpMaximize)
    createConstraints(problem, lambdaVariable)
    problem.setObjective(lambdaVariable)
    checkPulpStatus(problem.solve(state.getSettings().getSolver()))
    lambdaOpt = lambdaVariable.value()

    freezingTowers = []
    for currentTower, towerName in towerNames.items():
        if currentTower.isFrozen():
            continue
        problem = LpProblem(towerName, LpMaximize)
        createConstraints(problem, lambdaOpt)
        problem.setObjective(createLpSum(currentTower.getChoiceClass(), choiceNames, choiceVariables)
                             - lambdaOpt * currentTower.getSpeed() - currentTower.getHeight())
        checkPulpStatus(problem.solve(state.getSettings().getSolver()))
        value = problem.objective.value()
        if not state.getSettings().isNonnegative(value):
            raise ValueError(str(value) + " negative while determining frozen state of " +
                             repr(currentTower))
        if state.getSettings().isClose(problem.objective.value(), 0):
            freezingTowers.append(currentTower)

    return (lambdaOpt, frozenset(freezingTowers))


def solveVoteSSR(vote, solverSettings):
    '''
    @type vote: vote.society.Vote
    @type solverSettings: vote.solver.SolverSettings
    @rtype vote.society.Lottery
    '''

    state = SSRState(vote, solverSettings)
    state.adjustTowerSpeeds()
    while not state.isFinished():
        (climbingTime, freezingTowers) = computeLambda(state)
        state.advance(climbingTime, freezingTowers)
    currentClassHeights = {tower.getChoiceClass(): tower.getHeight()
                           for tower in state.getTowers()}
    return findLottery(vote, currentClassHeights, state.getSettings())
