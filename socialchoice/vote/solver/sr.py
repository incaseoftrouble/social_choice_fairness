'''
Created on 9 Sep 2015

@author: Tobias Meggendorfer
'''
from vote.society import ChoiceClass, Agent
from vote.solver import SolverSettings
from itertools import ifilter
from pulp.pulp import LpProblem, LpVariable, lpSum
from pulp.constants import LpMaximize
from vote.solver.util import createLpSum, getUniqueNames, findLottery,\
    getAllSubsets, checkPulpStatus


class Tower(object):
    '''
    Basic tower class for use in SR-like algorithms
    '''

    def __init__(self, choiceClass, name=None):
        if not isinstance(choiceClass, ChoiceClass):
            raise TypeError(repr(choiceClass) + " is not a choice class")
        self.name = name
        self.choiceClass = choiceClass
        self.height = 0

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        if height < 0 or 1 < height:
            raise ValueError("Height must be between 0 and 1, " +
                             str(height) + " given")
        self.height = height

    def tryClimb(self, climberHeight):
        if climberHeight > self.height:
            self.setHeight(climberHeight)

    def getName(self):
        if self.name is not None:
            return self.name
        return str(self.getChoiceClass())

    def getChoiceClass(self):
        return self.choiceClass

    def __str__(self):
        return self.getName() + "@" + str(self.getHeight())

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
        self.setSpeed(speed)
        self.setHeight(0)

    def setSpeed(self, speed):
        if speed < 0:
            raise ValueError("Speed must be nonnegative")
        self.speed = speed

    def getSpeed(self):
        return self.speed

    def getAgent(self):
        return self.agent

    def getCurrentChoiceClass(self):
        return self.currentChoiceClass

    def advanceCurrentChoiceClass(self):
        if self.isFinished():
            return None
        self.currentChoiceClass = next(self._choiceClassIter, None)
        self.setHeight(0)
        return self.currentChoiceClass

    def isFinished(self):
        return self.currentChoiceClass is None

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        if height < 0 or 1 < height:
            raise ValueError("Height must be between 0 and 1")
        self.height = height

    def __str__(self):
        if self.isFinished():
            return str(self.getAgent()) + "(F)"
        return str(self.getAgent()) + ":" + str(self.getCurrentChoiceClass()) + \
            "@" + str(self.getHeight()) + "/" + str(self.getSpeed())

    def __eq__(self, other):
        if isinstance(other, AgentData):
            return self.getAgent() == other.getAgent()
        return False

    def __hash__(self):
        return hash(self.getAgent())


class SRState(object):
    '''
    This class gathers all data occuring over an invocation of SR and performs low level tasks like climbing towers
    '''

    def __init__(self, vote, settings):
        if not isinstance(settings, SolverSettings):
            raise TypeError(repr(settings) + " is not a settings instance")
        self.time = 0
        self.settings = settings
        self.vote = vote
        self.towers = dict()
        self.agents = dict()
        for agent in vote.getAgents():
            self.agents[agent] = AgentData(agent, 1)

    def getTower(self, choiceClass):
        tower = self.towers.get(choiceClass, None)
        if tower is None:
            tower = Tower(choiceClass)
            self.towers[choiceClass] = tower
        return tower

    def advance(self, climbingTime, bouncingAgents):
        for agentData in self._getActiveAgentData():
            currentClass = agentData.getCurrentChoiceClass()
            tower = self.getTower(currentClass)
            climbedHeight = agentData.getHeight() + climbingTime * \
                agentData.getSpeed()
            if not self.settings.isInInterval(climbedHeight, 0, 1):
                raise ValueError(str(agentData) + " wants to push " +
                                 str(tower) + " to height " + climbedHeight)
            climbedHeight = self.settings.bound(climbedHeight, 0, 1)
            tower.tryClimb(climbedHeight)
            if agentData.getAgent() in bouncingAgents:
                agentData.advanceCurrentChoiceClass()
            else:
                agentData.setHeight(climbedHeight)

    def getSettings(self):
        return self.settings

    def getChoices(self):
        return self.vote.getChoices()

    def getTime(self):
        return self.time

    def getAgentSpeeds(self):
        '''
        Returns a dictionary of the form {agent: current speed}

        @rtype: dict(vote.society.Agent, float)
        '''
        return {agentData.getAgent(): agentData.getSpeed()
                for agentData in self._getActiveAgentData()}

    def _getAgentData(self, agent):
        if agent not in self.agents:
            raise ValueError("Agent " + repr(agent) + " not known")
        return self.agents[agent]

    def setClassHeight(self, choiceClass, height):
        self.getTower(choiceClass).setHeight(height)

    def setAgentHeight(self, agent, height):
        if not self.settings.isInInterval(height, 0, 1):
            raise ValueError(
                "Height must be between 0 and 1 (" + str(height) + " given)")
        if isinstance(agent, Agent):
            data = self._getAgentData(agent)
        elif isinstance(agent, AgentData):
            data = agent
        else:
            raise TypeError("Invalid argument " + repr(agent))
        data.setHeight(self.getSettings().bound(height, 0, 1))

    def setAgentSpeed(self, agent, speed):
        self._getAgentData(agent).setSpeed(speed)

    def getAgents(self):
        return self.vote.getAgents()

    def getActiveAgents(self):
        return map(lambda data: data.getAgent(), self._getActiveAgentData())

    def getAgentHeight(self, agent):
        return self.agents[agent].getHeight()

    def getAgentSpeed(self, agent):
        return self.agents[agent].getSpeed()

    def getCurrentAgentChoiceClass(self, agent):
        return self.agents[agent].getCurrentChoiceClass()

    def getAgentData(self, agent):
        return (self.getCurrentAgentChoiceClass(agent), self.getAgentHeight(agent), self.getAgentSpeed(agent))

    def _getActiveAgentData(self):
        return ifilter(lambda data: not data.isFinished(), self.agents.values())

    def getCurrentAgentChoiceClasses(self):
        '''
        Returns a dictionary of the form {agent: current choice class}

        @rtype: dict(vote.society.Agent, vote.society.ChoiceClass)
        '''
        return {agentData.getAgent(): agentData.getCurrentChoiceClass()
                for agentData in self._getActiveAgentData()}

    def getCurrentClassHeights(self):
        '''
        Returns a dictionary of the form {choice class: height}

        @rtype: dict(vote.society.ChoiceClass, float) 
        '''
        return {tower.getChoiceClass(): tower.getHeight() for tower in
                ifilter(lambda tower: tower.getHeight() > 0, self.towers.values())}

    def getChoiceClasses(self):
        return [tower.getChoiceClass() for tower in self.towers.values()]

    def getClassHeight(self, choiceClass):
        return self.getTower(choiceClass).getHeight()

    def isFinished(self):
        for agentData in self.agents.values():
            if not agentData.isFinished():
                return False
        return True

    def __str__(self):
        return "Agents: " + ",".join(map(str, sorted(self.agents.values(),
                                                     key=lambda data: data.getAgent().getName()))) + "\n" + \
            "Classes: " + ",".join(map(str, sorted(self.towers.values(),
                                                   key=lambda tower: tower.getChoiceClass())))


def computeLambda(state, maximumTime=1.0):
    activeAgents = state.getActiveAgents()
    agentNames = getUniqueNames(activeAgents, prefix="Agent ")
    classNames = getUniqueNames(state.getChoiceClasses(), prefix="Class ")
    choiceNames = getUniqueNames(state.getChoices(), prefix="")

    choiceVariables = LpVariable.dicts("p", choiceNames.values(), lowBound=0)
    lambdaVariable = LpVariable("l", lowBound=0.0, upBound=maximumTime)

    def createConstraints(problem, variable):
        problem += lpSum(choiceVariables) <= 1, "Distribution"
        for choiceClass, height in state.getCurrentClassHeights().items():
            problem += createLpSum(choiceClass, choiceNames, choiceVariables) >= \
                height, classNames[choiceClass] + " height"
        for agent in state.getActiveAgents():
            problem += createLpSum(state.getCurrentAgentChoiceClass(agent),
                                   choiceNames, choiceVariables) >= \
                state.getAgentHeight(agent) + variable * state.getAgentSpeed(agent), \
                agentNames[agent] + " push"

    problem = LpProblem("Lambda", LpMaximize)
    createConstraints(problem, lambdaVariable)
    problem.setObjective(lambdaVariable)
    checkPulpStatus(problem.solve(state.getSettings().getSolver()))
    lambdaOpt = lambdaVariable.value()

    bouncingAgents = []
    for currentAgent in activeAgents:
        problem = LpProblem(agentNames[currentAgent], LpMaximize)
        createConstraints(problem, lambdaOpt)
        (choiceClass, height, speed) = state.getAgentData(currentAgent)
        problem.setObjective(createLpSum(choiceClass, choiceNames, choiceVariables)
                             - lambdaOpt * speed - height)
        checkPulpStatus(problem.solve(state.getSettings().getSolver()))
        value = problem.objective.value()
        if not state.getSettings().isNonnegative(value):
            raise ValueError(str(value) + " negative while determining bounce of " +
                             repr(currentAgent) + " from " + repr(choiceClass) +
                             "@" + str(height) + "/" + str(speed))
        if state.getSettings().isClose(value, 0):
            bouncingAgents.append(currentAgent)
    return (lambdaOpt, bouncingAgents)


def solveVoteESR(vote, solverSettings):
    '''
    @type vote: vote.society.Vote
    @type solverSettings: vote.solver.SolverSettings
    @rtype vote.society.Lottery
    '''

    state = SRState(vote, solverSettings)

    while not state.isFinished():
        (climbTime, bouncingAgents) = computeLambda(state)
        state.advance(climbTime, bouncingAgents)
    return findLottery(vote, state.getCurrentClassHeights(), state.getSettings())


def solveVotePSR(vote, solverSettings):
    '''
    @type vote: vote.society.Vote
    @type solverSettings: vote.solver.SolverSettings
    @rtype vote.society.Lottery
    '''

    state = SRState(vote, solverSettings)

    agentChoiceClasses = state.getCurrentAgentChoiceClasses()
    for agent, choiceClass in agentChoiceClasses.items():
        speed = 0
        for otherChoiceClass in agentChoiceClasses.values():
            if otherChoiceClass.isSubsetOf(choiceClass):
                speed += 1
        state.setAgentSpeed(agent, speed)
    # As shown, no freeze happens between 0 and 1/n, thus one can simply
    # advance 1/n
    state.advance(1.0 / vote.getAgentCount(), [])
    for agent in state.getAgents():
        state.setAgentSpeed(agent, 1)
    while not state.isFinished():
        (climbTime, bouncingAgents) = computeLambda(state)
        state.advance(climbTime, bouncingAgents)
    return findLottery(vote, state.getCurrentClassHeights(), state.getSettings())


def solveVoteSPSR(vote, solverSettings):
    '''
    @type vote: vote.society.Vote
    @type solverSettings: vote.solver.SolverSettings
    @rtype vote.society.Lottery
    '''

    state = SRState(vote, solverSettings)

    for choiceClass in map(lambda choices: ChoiceClass(choices),
                           getAllSubsets(vote.getChoices())):
        height = 0.0
        agents = []
        for agent, agentChoiceClass in state.getCurrentAgentChoiceClasses().items():
            if agentChoiceClass.isSubsetOf(choiceClass):
                height += 1
            if agentChoiceClass == choiceClass:
                agents.append(agent)
        height /= vote.getAgentCount()
        state.setClassHeight(choiceClass, height)
        for agent in agents:
            state.setAgentHeight(agent, height)

    while not state.isFinished():
        (climbTime, bouncingAgents) = computeLambda(state)
        state.advance(climbTime, bouncingAgents)
    return findLottery(vote, state.getCurrentClassHeights(), state.getSettings())
