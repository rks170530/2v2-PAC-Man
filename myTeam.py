# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
from baselineTeam import ReflexCaptureAgent
import random, time, util
from game import Directions
import game


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='Offense', second='Defense'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class DummyAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).

        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)

        IMPORTANT: This method may run for at most 15 seconds.
        """

        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)

        '''
        Your initialization code goes here, if you need any.
        '''

    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        """
        actions = gameState.getLegalActions(self.index)

        '''
        You should change this in your own agent.
        '''

        return random.choice(actions)


class IDKAgent(ReflexCaptureAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.weights = util.Counter()
        self.weights = {
            'score': 100,  # pick up food
            'distanceToFood': -1,  # get close to food
            'distanceToCapsule': -1,  # get close to capsules
            'safeDistance': -10,  # return to start
            'avoidDeadEnd': -100,  # avoid dead end
            # 'attack': 10,                     # TODO attack scared ghosts and pacmen
            'ghostDistance': 100,  # avoid ghosts
            # 'ScaredGhostDistance': -100,
            # get close to scared ghosts -- don't do, stall out scared timer to do whatever you want
            'enemyPacmanDistance': -1,  # get close to pacmen
            'stop': -100,  # avoid staying still
            'reverse': -2  # avoid going backwards
        }

    def getFeatures(self, gameState, action):
        features = util.Counter()
        current = self.getCurrentObservation()
        successor = self.getSuccessor(gameState, action)

        currentState = current.getAgentState(self.index)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        foodList = self.getFood(successor).asList()
        capsuleList = self.getCapsules(successor)

        # value capturing food
        features['score'] = myState.numCarrying + self.getScore(successor)

        capsuleDistance = []
        for capsule in capsuleList:
            capsuleDistance.append(self.getMazeDistance(myPos, capsule))
        if len(capsuleDistance) > 0:
            smallestDist = min(capsuleDistance)
            features['distanceToCapsule'] = smallestDist

        if current is not None and myPos in self.getCapsules(current):
            features['distanceToCapsule'] = -100000

        enemies = [current.getAgentState(i) for i in self.getOpponents(current)]
        enemyPacmen = [e for e in enemies if e.isPacman and e.getPosition() is not None]
        ghosts = [g for g in enemies if not g.isPacman and
                  g.getPosition() is not None and not g.scaredTimer > 0]
        scaredGhosts = [g for g in enemies if not g.isPacman and g.getPosition() is not None and g.scaredTimer > 0]

        # run from ghosts
        ghostDistances = []
        for ghost in ghosts:
            ghostDistances.append(self.getMazeDistance(myPos, ghost.getPosition()))
        if myState.isPacman and len(ghostDistances) > 0:
            smallestDist = min(ghostDistances)
            if smallestDist < 5:
                features['avoidDeadEnd'] = 1 if len(successor.getLegalActions(self.index)) < 3 else 0
            if smallestDist < 4:
                features['safeDistance'] = self.getMazeDistance(myPos, self.start)
            if smallestDist < 3:
                features['ghostDistance'] = smallestDist

        # chase scared ghosts
        # scaredGhostDistances = []
        # for ghost in scaredGhosts:
        #     scaredGhostDistances.append((self.getMazeDistance(myPos, ghost.getPosition()), ghost))
        # if myState.isPacman and len(scaredGhostDistances) > 0:
        #     smallestDist, ghost = min([scaredGhostDistances[0]])
        #     # features['ScaredGhostDistance'] = smallestDist

        # if len(scaredGhostDistances) > 0 and \
        #         current is not None and \
        #         myPos in [current.getAgentPosition(i) for i in
        #                   self.getOpponents(current)]:
        #     features['ScaredGhostDistance'] = -100

        # chase pacman if not scared
        enemyPacmenDistances = []
        for pacman in enemyPacmen:
            enemyPacmenDistances.append(self.getMazeDistance(myPos, pacman.getPosition()))
        if len(enemyPacmenDistances) > 0:
            smallestDist = min(enemyPacmenDistances)
            if myState.scaredTimer <= 0:
                features['enemyPacmanDistance'] = smallestDist
            else:
                if smallestDist < 3:
                    features['enemyPacmanDistance'] = -smallestDist
                features['avoidDeadEnd'] = 1 if len(successor.getLegalActions(self.index)) < 3 else 0

        if currentState.numCarrying > 2:
            features['safeDistance'] = self.getMazeDistance(myPos, self.start) * (
                    myState.numCarrying / (float(len(foodList) + 1)))

        if len(foodList) > 0:  # This should always be True,  but better safe than sorry
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        if action == Directions.STOP:
            features['stop'] = 1

        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev:
            features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return self.weights


class Defense(IDKAgent):
    def __init__(self, index):
        IDKAgent.__init__(self, index)
        self.weights['enemyPacmanDistance'] = -100  # focus on defense
        # TODO avoid being too aggressive and leave defense open


class Offense(IDKAgent):
    def __init__(self, index):
        IDKAgent.__init__(self, index)
        self.weights['enemyPacmanDistance'] = -.75  # care less about defending
        self.weights['score'] = 150  # value score more
        self.weights['previous'] = -50  # avoid backtracking to avoid circle stalemates

    def getFeatures(self, gameState, action):
        features = IDKAgent.getFeatures(self, gameState, action)
        previousLocations = self.getPreviousLocations(8)
        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()
        if myPos in previousLocations:
            features['previous'] = 1
        return features

    def getPreviousLocations(self, t):
        return [state.getAgentState(self.index).getPosition() for state in self.observationHistory[-t:]]
