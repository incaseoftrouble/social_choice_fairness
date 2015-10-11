'''
This package contains all basic objects related to social choice / assigment problems and their solution

Created on 8 Sep 2015

@author: Tobias Meggendorfer
'''
import collections
import math
from functools import total_ordering


@total_ordering
class Choice(object):
    '''
    Wrapper class for choice objects
    '''

    def __init__(self, choiceObject, name=None):
        '''
        Constructor

        @type choiceObject: collections.Hashable 
        '''
        if not isinstance(choiceObject, collections.Hashable):
            raise TypeError(repr(choiceObject) + " is not hashable")
        self.choiceObject = choiceObject
        if name is not None:
            self.name = str(name)
        else:
            self.name = str(choiceObject)

    def getObject(self):
        '''
        Returns the assoicated object

        @rtype: object
        '''
        return self.choiceObject

    def getName(self):
        return self.name

    def __str__(self):
        return self.getName()

    def __repr__(self):
        return "Choice(" + self.getName() + ": " + repr(self.getObject()) + ")"

    def __eq__(self, o):
        if isinstance(o, Choice):
            return self.getObject() == o.getObject()
        return False

    def __lt__(self, o):
        return self.getObject() < o.getObject()

    def __hash__(self):
        return hash(self.getObject())


@total_ordering
class ChoiceClass(object):
    '''
    Class containing multiple choices
    '''

    def __init__(self, choices):
        '''
        Constructor

        :param choices: A set of all choices in this class

        :type choices: Choice|list(Choice)
        '''
        if isinstance(choices, Choice):
            self.choices = frozenset(choices)
        elif isinstance(choices, collections.Iterable):
            for choice in choices:
                if not isinstance(choice, Choice):
                    raise TypeError("Object " + repr(choice) +
                                    " is not a Choice")
            self.choices = frozenset(choices)
        else:
            raise TypeError("Can't handle " + repr(choice))

    def getChoices(self):
        '''
        Returns the choices in this class

        :rtype: set(Choice)
        '''
        return self.choices

    def __str__(self):
        return "(" + ",".join(map(str, sorted(self.getChoices()))) + ")"

    def __repr__(self):
        return "ChoiceClass(" + ",".join(map(repr, self.getChoices())) + ")"

    def __iter__(self):
        return iter(self.getChoices())

    def __len__(self):
        return len(self.getChoices())

    def __lt__(self, other):
        selfLength = len(self)
        otherLength = len(other)
        if(selfLength < otherLength):
            return True
        if(selfLength > otherLength):
            return False
        for selfItem, otherItem in zip(self.getChoices(), other.getChoices()):
            if selfItem < otherItem:
                return True
            if selfItem > otherItem:
                return False
        return False

    def __hash__(self):
        return hash(self.choices)

    def __eq__(self, other):
        if isinstance(other, ChoiceClass):
            return self.getChoices() == other.getChoices()
        return False

    def __contains__(self, item):
        return item in self.getChoices()

    def isSubsetOf(self, other):
        '''
        Determines wether this class is contained in the other class

        :type other: ChoiceClass|set(Choice)

        :rtype: bool
        '''
        if isinstance(other, ChoiceClass):
            return self.getChoices().issubset(other.getChoices())
        elif isinstance(other, collections.Set):
            return self.getChoices().issubset(other)
        elif isinstance(other, collections.Iterable):
            for element in self.getChoices():
                if element not in other:
                    return False
            return True
        raise ValueError("Can't handle " + repr(other))


class Preference(object):
    '''
    This class wraps preferences
    '''

    def __init__(self, choiceClasses):
        if not isinstance(choiceClasses, collections.Iterable):
            raise TypeError(repr(choiceClasses) + " is not iterable")
        for choiceClass in choiceClasses:
            if not isinstance(choiceClass, ChoiceClass):
                raise TypeError(
                    repr(choiceClasses) + " is not a list of choice classes")
        self.classes = tuple(choiceClasses)

    def getChoiceClasses(self):
        return self.classes

    def isStrict(self):
        for choiceClass in self.getChoiceClasses():
            if len(choiceClass) > 1:
                return False
        return True

    def getChoiceClass(self, index):
        if index >= len(self.getChoiceClasses()):
            return None
        return self.getChoiceClasses()[index]

    def __len__(self):
        return len(self.getChoiceClasses())

    def __getitem__(self, key):
        return self.getChoiceClasses()[key]

    def __iter__(self):
        return iter(self.getChoiceClasses())

    def __str__(self):
        return ",".join(["(" + ",".join(map(str, sorted(choiceClass.getChoices()))) + ")"
                         for choiceClass in self.getChoiceClasses()])

    def __repr__(self):
        return "Preference: " + ",".join(["(" + ",".join(map(str, sorted(choiceClass.getChoices()))) + ")"
                                          for choiceClass in self.getChoiceClasses()])


class Agent(object):
    '''
    This class represents an agent of a social choice or assignment problem
    '''

    def __init__(self, identifier, preference, name=None):
        if not isinstance(preference, Preference):
            raise TypeError(repr(preference) + " is not a preference")
        if identifier is None:
            raise ValueError("Agent identifier is none")
        if not isinstance(identifier, collections.Hashable):
            raise TypeError(repr(identifier) + " is not hashable")

        self.identifier = identifier
        self.preference = preference
        if name is not None:
            self.name = str(name)
        else:
            self.name = str(identifier)

    def getName(self):
        '''
        Returns the name of the agent

        :rtype: str
        '''
        return self.name

    def getIdentifier(self):
        return self.identifier

    def getChoiceClasses(self):
        return self.getPreference().getChoiceClasses()

    def getPreference(self):
        return self.preference

    def __str__(self):
        return self.getName()

    def __repr__(self):
        return "Agent[" + self.getName() + ": " + repr(self.preference) + "]"

    def __eq__(self, other):
        if isinstance(other, Agent):
            return self.getIdentifier() == other.getIdentifier()
        return False


class Vote(object):
    '''
    This class gathers all information needed for a vote, i.e. the set of all choices and all agents with their preferences
    '''

    def __init__(self, agents, name=None):
        choices = list()
        for agent in agents:
            if not isinstance(agent, Agent):
                raise TypeError(repr(agent) + " is no agent")
        for agent in agents:
            for choiceClass in agent.getChoiceClasses():
                choices.extend(choiceClass)
        choices = frozenset(choices)
        for agent in agents:
            for choiceClass in agent.getChoiceClasses():
                for choice in choiceClass:
                    if choice not in choices:
                        raise ValueError("Agent " + str(agent) +
                                         + " has incomplete preferences (" +
                                         + repr(choice) + " is missing)")
        self.choices = choices
        self.agents = frozenset(agents)

    def getAgents(self):
        return self.agents

    def getChoices(self):
        return self.choices

    def getAgentCount(self):
        return len(self.getAgents())

    def getChoiceCount(self):
        return len(self.getChoices())

    def __str__(self):
        return "Agents: " + ",".join(sorted(map(str, self.getAgents()))) + \
            "; Choices: " + ",".join(sorted(map(str, self.getChoices()))) + \
            "\n  " + \
            "\n  ".join([agent.getName() + ": " + str(agent.getPreference())
                         for agent in sorted(self.getAgents(), key=lambda x: x.getName())])


class Lottery(object):
    '''
    This class represents a probability distribution
    '''

    def __init__(self, distribution, solverSettings):
        self.distribution = dict()
        for obj, value in distribution.items():
            self.distribution[obj] = solverSettings.checkBound(value, 0, 1)
        assert solverSettings.isClose(math.fsum(self.distribution.values()), 1)

    def getValue(self, obj):
        return self.distribution[obj]

    def getObjects(self):
        return self.distribution.keys()

    def getDistribution(self):
        return self.distribution.items()

    def __len__(self):
        return len(self.getDistribution())

    def __getitem__(self, key):
        return self.getValue(key)

    def __str__(self):
        return ", ".join("{object}:{prob:1.6f}".format(object=obj, prob=value)
                         for obj, value in sorted(self.distribution.items(),
                                                  key=lambda (obj, value): str(obj)))


class Assignment(object):

    def __init__(self, assignment):
        for agent in assignment.keys():
            assert isinstance(agent, Agent)
        self.assignment = assignment

    def __eq__(self, other):
        if isinstance(other, Assignment):
            return cmp(self.assignment, other.assignment) == 0
        return False

    def __hash__(self):
        return hash(frozenset(self.assignment.items()))

    def __len__(self):
        return len(self.assignment)

    def __getitem__(self, key):
        return self.getAssignment(key)

    def __str__(self):
        return "[" + " ".join(agent.getName() + ":" + str(assignment)
                              for agent, assignment
                              in sorted(self.assignment.items(),
                                        key=lambda (agent, assignment): agent.getName())) + \
            "]"

    def __repr__(self):
        return "Assignment[" + " ".join(repr(agent) + ":" + repr(assignment)
                                        for agent, assignment
                                        in sorted(self.assignment.items(),
                                                  key=lambda (agent, assignment): agent.getName())) + \
            "]"

    def getAssignment(self, agent):
        return self.assignment[agent]

    def getAgents(self):
        return self.assignment.keys()

    def getObjects(self):
        return self.assignment.values()

    def getAgentObjectPairs(self):
        return self.assignment.items()


class AssignmentLottery(object):

    def __init__(self, assignments, solverSettings):
        if isinstance(assignments, Lottery):
            agentLotteries = dict()
            objects = set()
            agents = set()
            for assignment in assignments.getObjects():
                assert isinstance(assignment, Assignment)
                objects.update(assignment.getObjects())
                agents.update(assignment.getAgents())
                assert len(objects) == len(assignment)
                assert len(agents) == len(assignment)
            for agent in agents:
                agentLotteries[agent] = {obj: 0.0 for obj in objects}
            for assignment, probability in assignments.getDistribution():
                for agent, obj in assignment.getAgentObjectPairs():
                    agentLotteries[agent][obj] += probability
            agentLotteries = {agent: Lottery(agentLottery, solverSettings)
                              for agent, agentLottery in agentLotteries.items()}
            self.lotteries = agentLotteries
        else:
            raise TypeError("Can't process " + repr(assignments))

    def getProbability(self, agent, obj):
        return self.lotteries[agent][obj]

    def getAgentDistribution(self, agent):
        return self.lotteries[agent].getDistribution()

    def __str__(self):
        return "\n".join(str(agent) + ": " + str(lottery)
                         for agent, lottery
                         in sorted(self.lotteries.items(), key=lambda (agent, _): agent.getName()))
