'''
Created on 9 Sep 2015

@author: tlm
'''

from vote.parser import parseVoteFromDict, toAssigmentVote
from vote.solver.sr import solveVoteESR, solveVotePSR, solveVoteSPSR
from vote.solver.settings import SolverSettings
from pulp.solvers import PULP_CBC_CMD
from vote.solver.ssr import solveVoteSSR
from vote.society import AssignmentLottery

if __name__ == '__main__':
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"

    #vote = {
    #    1: [(A, B), (F, D, C, E)],
    #    2: [(F, A), (C, E), (D, B)],
    #    3: [(F, D, A, C), (B, E)],
    #}
    vote = {
        1: [(A), (B, C)],
        2: [(B), (A), (C)],
        3: [(A, C), (B)],
    }

    vote = parseVoteFromDict(vote)
    print str(vote)
    vote = toAssigmentVote(vote)
    print str(vote)

    settings = SolverSettings(solver=PULP_CBC_CMD(msg=False),
                              absoluteTolerance=10 ** -5,
                              relativeTolerance=10 ** -5)
    lotteryESR = solveVoteESR(vote, settings)
    print "ESR:\n" + str(lotteryESR)
    lotteryPSR = solveVotePSR(vote, settings)
    print "PSR:\n" + str(lotteryPSR)
    lotterySPSR = solveVoteSPSR(vote, settings)
    print "SPSR:\n" + str(lotterySPSR)
    lotterySSR = solveVoteSSR(vote, settings)
    print "SSR:\n" + str(lotterySSR)
