'''
Created on 8 Sep 2015

@author: Tobias Meggendorfer
'''
from vote.society import Choice, ChoiceClass, Agent, Preference, Vote,\
    Assignment
from itertools import permutations


def toAssignmentVote(vote):
    objects = set(map(lambda choice: choice.getObject(),
                      vote.getChoices()))
    agents = list(vote.getAgents())

    assigmentAgents = []
    for i in range(len(agents)):
        agent = agents[i]
        assignmentClasses = []
        for choiceClass in agent.getChoiceClasses():
            objectsInClass = set(map(lambda choice: choice.getObject(),
                                     choiceClass.getChoices()))
            assignmentClass = []
            for permutation in permutations(objects):
                if permutation[i] not in objectsInClass:
                    continue
                assigment = Choice(Assignment({agents[j]: permutation[j]
                                               for j in range(len(agents))}))
                assignmentClass.append(assigment)
            assignmentClasses.append(ChoiceClass(assignmentClass))
        assigmentAgents.append(Agent(agent.getIdentifier(),
                                     Preference(assignmentClasses),
                                     agent.getName()))
    return Vote(assigmentAgents)


def parseVoteFromDict(choiceDict,
                      addMissingChoices=True,
                      removeDuplicateChoices=True):
    '''
    Parses a vote from a dict of the form <agent name>: [(a, b, c), d, e ]

    :type choiceDict: dict(object, list(tuple(object)))
    :type addMissingChoices: bool
    :type removeDuplicateChoices: bool
    :rtype: Vote
    '''
    saneChoiceDict = dict()
    allChoices = set()

    for agent, choiceClasses in choiceDict.items():
        saneAgentChoiceClasses = []
        for choiceClass in choiceClasses:
            if isinstance(choiceClass, tuple) or \
                    isinstance(choiceClass, set) or \
                    isinstance(choiceClass, list):
                choiceClass = set(choiceClass)
            else:
                choiceClass = set([choiceClass])
            allChoices.update(choiceClass)
            saneAgentChoiceClasses.append(choiceClass)
        saneChoiceDict[agent] = saneAgentChoiceClasses
    for agent, choiceClasses in saneChoiceDict.items():
        agentChoices = set()
        for choiceClass in choiceClasses:
            if not agentChoices.isdisjoint(choiceClass):
                if not removeDuplicateChoices:
                    raise ValueError("Duplicate choices for agent " +
                                     str(agent))
            choiceClass.difference_update(agentChoices)
            agentChoices.update(choiceClass)

        diff = allChoices.difference(agentChoices)
        if diff:
            if addMissingChoices:
                choiceClasses.append(diff)
            else:
                raise ValueError("Missing choices " + str(diff) +
                                 " for agent " + str(agent))

    agents = set()

    for agent, choiceClasses in saneChoiceDict.items():
        parsedChoiceClasses = []
        for choiceClass in choiceClasses:
            choiceClass = ChoiceClass(
                [Choice(choice) for choice in choiceClass])
            parsedChoiceClasses.append(choiceClass)
        preference = Preference(parsedChoiceClasses)
        agent = Agent(agent, preference)
        agents.add(agent)

    vote = Vote(agents)
    return vote
