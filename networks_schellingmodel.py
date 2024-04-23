import random
import numpy as np
import matplotlib.pyplot as plt
from seaborn import heatmap, lineplot
from matplotlib import animation

class Node():
    '''
    Singular node object, contains functionality for coloring in nodes.
    Empty nodes are encoded as white.
    Arguments:
        color: 'red', 'blue' or 'white'.
        x: integer x value, used for distance calc.
        y: integer y value, used for distance calc.
    '''
    def __init__(self, color, x, y):
        self.color =  color
        self.x = x
        self.y = y
        self.neigh = set()
        self.pval = 0
        self.redval = 0
        self.blueval = 0
        self.update()
    
    def update(self):
        '''
        Updates nodes pval(how satisfied it is) and returns new pval.
        Empty cells have pval of 1 by convention.

        Returns:
            self.pval
        '''
        redcount = 0
        bluecount = 0
        for n in self.neigh:
            if (n.color == 'blue'):
                bluecount += 1
            elif (n.color == 'red'):
                redcount += 1

        if redcount+bluecount == 0:
            self.pval = 1
            self.redval = 1
            self.blueval = 1
            return self.pval
        
        self.redval = redcount/(redcount+bluecount)
        self.blueval = bluecount/(redcount+bluecount)

        if self.color == 'white':
            self.pval = 1
        elif self.color == 'red':
            self.pval = self.redval
        else:
            self.pval = self.blueval
        
        return self.pval

    def setcolor(self, color):
        '''
        Sets the color of a node.
        Arguments:
            color: 'red', 'blue' or 'white'.
        '''
        self.color = color

    def color_and_update(self, color, pbound):
        '''
        Colors in node and updates all neighbors. Returns neighbors below bound.
        Originally implemented for localized updating optimization, deprecated as
        of current implementation.

        'Premature optimization is the root of all evil.' - Donald Knuth

        Arguments:
            color: 'red', 'blue' or 'white'.
            pbound: float, value below which nodes are unsatisfied.
        Returns:
            unsatisfied: list of unsatisfied neighbors, including itself.
        '''

        self.color = color
        self.update()

        unsatisfied = []
        for n in self.neigh:
            npval = n.update()
            if npval < pbound and n.color != 'white':
                unsatisfied.append(n)
        if self.pval < pbound and self.color != 'white':
            unsatisfied.append(self)

        return unsatisfied

def distance(n1, n2):
    '''
    Distance calculation helper function.
    Arguments:
        n1, n2: The nodes between which to calculate the distance.
    Returns:
        distance: float, Euclidean distance.
    '''
    return ((n1.x-n2.x)**2+(n1.y-n2.y)**2)**0.5

def bind_nodes(n1, n2):
    '''
    Makes nodes neighbors, and updates each node.
    '''
    n1.neigh.add(n2)
    n2.neigh.add(n1)
    n1.update()
    n2.update()

class Board():
    '''
    The main game object.
    Arguments:
        size: integer, size of one side of the game board.
        whiteP: float, percent of empty nodes.
        redP: float, percent of red nodes. Blue nodes are remainder not white or red.
        pbound: float, value below which nodes are unsatisfied.
        stopping: float optional, for 'closest' assignment algorithm. Stops if the
            number of unsatisfied nodes is below stopping. Avoids getting stuck.
            If running 'closest' assignments, keep in the 5-20 range.
    '''
    def __init__(self, size, whiteP, redP, pbound, stopping = 1):
        self.size = size
        self.pbound = pbound
        self.white_count = int(size**2*whiteP)
        self.red_count = int(size**2*redP*(1-whiteP))
        self.blue_count = size**2 - self.red_count - self.white_count
        self.unsatisfied = []
        self.whiteCells = []
        self.board = self.build_board()
        self.animationList = []
        self.stopping = stopping
    
    def reload_sets(self):
        '''
        Scan board and rebould the unsatisfied and whiteCells sets.
        '''
        new_whiteCells = []
        new_unsatisfied = []

        for row in self.board:
            for node in row:
                pval = node.update()
                if node.color == 'white':
                    new_whiteCells.append(node)
                elif pval < self.pbound:
                    new_unsatisfied.append(node)

        self.unsatisfied = new_unsatisfied
        self.whiteCells = new_whiteCells

    def sample_color(self):
        '''
        Returns one of the available colors. Helper for building the board.
        '''
        color = random.sample(['white', 'red', 'blue'], counts=[self.white_count, self.red_count, self.blue_count], k=1)[0]
        if color == 'white':
            self.white_count -= 1
        elif color == 'red':
            self.red_count -= 1
        elif color == 'blue':
            self.blue_count -= 1
        return color
    
    def build_board(self):
        '''
        Builds board list of nodes. Returns board list.
        '''

        ### Build (0,0)
        board = [[Node(self.sample_color(), 0, 0)]]

        ### Build first row
        for _ in range(1, self.size):
            new_node = Node(self.sample_color(), 0, _)
            bind_nodes(board[0][_-1], new_node)
            board[0].append(new_node)
        
        ### Build rest of board
        for i in range(1, self.size):
            board.append([])
            for j in range(self.size):
                new_node = Node(self.sample_color(), i, j)
                if j == 0:
                    bind_nodes(board[i-1][j+1], new_node)
                elif j == self.size - 1:
                    bind_nodes(board[i][j-1], new_node)
                    bind_nodes(board[i-1][j-1], new_node)
                else:
                    bind_nodes(board[i][j-1], new_node)
                    bind_nodes(board[i-1][j-1], new_node)
                    bind_nodes(board[i-1][j+1], new_node)

                bind_nodes(board[i-1][j], new_node)
                board[i].append(new_node)

        ### Build initial unsatisfied and whiteCells lists
        for row in board:
            for node in row:
                pval = node.update()
                if node.color == 'white':
                    self.whiteCells.append(node)
                elif pval < self.pbound:
                    self.unsatisfied.append(node)

        return board

    def step_single_random(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        Empty = random.sample(self.whiteCells, k=1)[0]

        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())

        return True

    def step_single_randomSat_stop(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        random.shuffle(self.whiteCells)
        Empty = None
        color = Moving.color
        
        ### Find Satisfying
        if color == 'red':
            for Candidate in self.whiteCells:
                if Candidate.redval >= self.pbound:
                    Empty = Candidate
                    break
        elif color == 'blue':
            for Candidate in self.whiteCells:
                if Candidate.blueval >=self.pbound:
                    Empty = Candidate
                    break
        
        ### No candidate for current color, try other color
        if Empty == None:
            # print(f"CANT FIND SPOT FOR {color} CELL")
            for OtherMoving in self.unsatisfied:
                otherColor = OtherMoving.color
                
                if otherColor == color:
                    continue

                if otherColor == 'red':
                    for Candidate in self.whiteCells:
                        if Candidate.redval >= self.pbound:
                            Moving = OtherMoving
                            Empty = Candidate
                            break
                elif otherColor == 'blue':
                    for Candidate in self.whiteCells:
                        if Candidate.blueval >=self.pbound:
                            Moving = OtherMoving
                            Empty = Candidate
                            break
                
                if Empty == None:
                    print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                    return False
        
        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())

        return True
                
    def step_single_randomSat_cont(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        random.shuffle(self.whiteCells)
        Empty = None
        color = Moving.color
        
        ### Find Satisfying
        if color == 'red':
            for Candidate in self.whiteCells:
                if Candidate.redval >= self.pbound:
                    Empty = Candidate
                    break
        elif color == 'blue':
            for Candidate in self.whiteCells:
                if Candidate.blueval >=self.pbound:
                    Empty = Candidate
                    break
        
        ### No candidate for current color, select random
        if Empty == None:
            # print(f"CANT FIND SPOT FOR {color} CELL")
            Empty = random.sample(self.whiteCells, k=1)[0]
        
        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())

        return True

    def step_single_closest(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
        Empty = self.whiteCells[0]
        if len(self.unsatisfied)<self.stopping:
            return False
        
        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_single_closestSat_stop(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
        Empty = None
        color = Moving.color
        if len(self.unsatisfied)<self.stopping:
            return False
        
        ### Find Satisfying
        if color == 'red':
            for Candidate in self.whiteCells:
                if Candidate.redval >= self.pbound:
                    Empty = Candidate
                    break
        elif color == 'blue':
            for Candidate in self.whiteCells:
                if Candidate.blueval >=self.pbound:
                    Empty = Candidate
                    break
        
        ### No candidate for current color, try other color
        if Empty == None:
            # print(f"CANT FIND SPOT FOR {color} CELL")
            for OtherMoving in self.unsatisfied:
                otherColor = OtherMoving.color
                
                if otherColor == color:
                    continue
                
                self.whiteCells.sort(key = lambda Node: distance(OtherMoving, Node))
                if otherColor == 'red':
                    for Candidate in self.whiteCells:
                        if Candidate.redval >= self.pbound:
                            Moving = OtherMoving
                            Empty = Candidate
                            break
                elif otherColor == 'blue':
                    for Candidate in self.whiteCells:
                        if Candidate.blueval >=self.pbound:
                            Moving = OtherMoving
                            Empty = Candidate
                            break
                
                if Empty == None:
                    print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                    return False
        
        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        # print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())

        return True
    
    def step_single_closestSat_cont(self):
        Moving = random.sample(self.unsatisfied, k=1)[0]
        self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
        Empty = None
        color = Moving.color
        if len(self.unsatisfied)<self.stopping:
            return False
        
        ### Find Satisfying
        if color == 'red':
            for Candidate in self.whiteCells:
                if Candidate.redval >= self.pbound:
                    Empty = Candidate
                    break
        elif color == 'blue':
            for Candidate in self.whiteCells:
                if Candidate.blueval >=self.pbound:
                    Empty = Candidate
                    break
        
        ### No candidate for current color, select closest
        if Empty == None:
            # print(f"CANT FIND SPOT FOR {color} CELL")
            Empty = self.whiteCells[0]
        
        Empty.setcolor(Moving.color)
        Moving.setcolor('white')
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))
        self.animationList.append(self.to_np_colorcode())

        return True
    
    def step_whitebatch_random(self):

        while (self.unsatisfied and self.whiteCells):
            Moving = random.sample(self.unsatisfied, k=1)[0]
            Empty = random.sample(self.whiteCells, k=1)[0]
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            self.whiteCells.append(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')

        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_random(self):

        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            Empty = random.sample(self.whiteCells, k=1)[0]
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True

    def step_whitebatch_randomSat_stop(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            random.shuffle(self.whiteCells)
            Empty = None
            color = Moving.color

            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, try other color
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                for OtherMoving in self.unsatisfied:
                    otherColor = OtherMoving.color
                    
                    if otherColor == color:
                        continue

                    if otherColor == 'red':
                        for Candidate in self.whiteCells:
                            if Candidate.redval >= self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    elif otherColor == 'blue':
                        for Candidate in self.whiteCells:
                            if Candidate.blueval >=self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    
                    if Empty == None:
                        print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                        return False
                    
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            self.whiteCells.append(Moving)
            
            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_randomSat_stop(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            random.shuffle(self.whiteCells)
            Empty = None
            color = Moving.color

            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, try other color
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                for OtherMoving in self.unsatisfied:
                    otherColor = OtherMoving.color
                    
                    if otherColor == color:
                        continue

                    if otherColor == 'red':
                        for Candidate in self.whiteCells:
                            if Candidate.redval >= self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    elif otherColor == 'blue':
                        for Candidate in self.whiteCells:
                            if Candidate.blueval >=self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    
                    if Empty == None:
                        print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                        return False
                    
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            
            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True

    def step_whitebatch_randomSat_cont(self):
        
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            random.shuffle(self.whiteCells)
            Empty = None
            color = Moving.color

            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, select random
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                Empty = random.sample(self.whiteCells, k=1)[0]
                    
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            self.whiteCells.append(Moving)
            
            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_randomSat_cont(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            random.shuffle(self.whiteCells)
            Empty = None
            color = Moving.color

            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, select random
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                Empty = random.sample(self.whiteCells, k=1)[0]
                    
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            
            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_whitebatch_closest(self):
        while (self.unsatisfied and self.whiteCells):

            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = self.whiteCells[0]
            if len(self.unsatisfied)<self.stopping:
                return False
            
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)
            self.whiteCells.append(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')

        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_closest(self):
        while (self.unsatisfied and self.whiteCells):

            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = self.whiteCells[0]
            if len(self.unsatisfied)<self.stopping:
                return False
            
            self.whiteCells.remove(Empty)
            self.unsatisfied.remove(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')

        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_whitebatch_closestSat_stop(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = None
            color = Moving.color
            
            if len(self.unsatisfied)<self.stopping:
                return False
            
            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, try other color
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                for OtherMoving in self.unsatisfied:
                    otherColor = OtherMoving.color
                    
                    if otherColor == color:
                        continue
                    
                    self.whiteCells.sort(key = lambda Node: distance(OtherMoving, Node))
                    if otherColor == 'red':
                        for Candidate in self.whiteCells:
                            if Candidate.redval >= self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    elif otherColor == 'blue':
                        for Candidate in self.whiteCells:
                            if Candidate.blueval >=self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    
                    if Empty == None:
                        print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                        return False
            
            self.unsatisfied.remove(Moving)
            self.whiteCells.remove(Empty)
            self.whiteCells.append(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_closestSat_stop(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = None
            color = Moving.color
            
            if len(self.unsatisfied)<self.stopping:
                return False
            
            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, try other color
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                for OtherMoving in self.unsatisfied:
                    otherColor = OtherMoving.color
                    
                    if otherColor == color:
                        continue
                    
                    self.whiteCells.sort(key = lambda Node: distance(OtherMoving, Node))
                    if otherColor == 'red':
                        for Candidate in self.whiteCells:
                            if Candidate.redval >= self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    elif otherColor == 'blue':
                        for Candidate in self.whiteCells:
                            if Candidate.blueval >=self.pbound:
                                Moving = OtherMoving
                                Empty = Candidate
                                break
                    
                    if Empty == None:
                        print(f"CATASTROPHIC STOP NO CELLS FOR RED OR BLUE!!!")
                        return False
            
            self.unsatisfied.remove(Moving)
            self.whiteCells.remove(Empty)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
        
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
     
    def step_whitebatch_closestSat_cont(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = None
            color = Moving.color
            
            if len(self.unsatisfied)<self.stopping:
                return False
            
            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, select closest
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                Empty = self.whiteCells[0]
                
            self.unsatisfied.remove(Moving)
            self.whiteCells.remove(Empty)
            self.whiteCells.append(Moving)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
            
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True
    
    def step_batch_closestSat_cont(self):
        while self.unsatisfied and self.whiteCells:
            Moving = random.sample(self.unsatisfied, k=1)[0]
            self.whiteCells.sort(key = lambda Node: distance(Moving, Node))
            Empty = None
            color = Moving.color
            
            if len(self.unsatisfied)<self.stopping:
                return False
            
            ### Find Satisfying
            if color == 'red':
                for Candidate in self.whiteCells:
                    if Candidate.redval >= self.pbound:
                        Empty = Candidate
                        break
            elif color == 'blue':
                for Candidate in self.whiteCells:
                    if Candidate.blueval >=self.pbound:
                        Empty = Candidate
                        break
            
            ### No candidate for current color, select closest
            if Empty == None:
                # print(f"CANT FIND SPOT FOR {color} CELL")
                Empty = self.whiteCells[0]
                
            self.unsatisfied.remove(Moving)
            self.whiteCells.remove(Empty)

            Empty.setcolor(Moving.color)
            Moving.setcolor('white')
            
        self.reload_sets()
        print(len(self.unsatisfied), len(self.whiteCells))

        self.animationList.append(self.to_np_colorcode())
        return True

    def to_np_pvals(self):
        '''
        Returns the pval of each node as a 2D numpy array.
        '''
        return np.array([[self.board[i][j].pval for j in range(self.size)] for i in range(self.size)])
    
    def to_np_colorcode(self):
        '''
        Returns a 2D numpy array encoding red cells as 100, blue as -100, and white as 0.
        '''
        values = []
        for i in range(self.size):
            current_row = []
            for j in range(self.size):
                current_node_color = self.board[i][j].color
                if current_node_color == 'white':
                    current_row.append(0)
                elif current_node_color == 'red':
                    current_row.append(100)
                else:
                    current_row.append(-100)
            values.append(current_row)
        return np.array(values)
    
    def run(self, iters, assignAlgorithm):
        '''
        Runs the simulation.
        Arguments:
            iters: integer, maximum number of iterations.
            assignAlgorithm: string, which assignment algorithm to use.
        Returns:
            i: integer, number of iterations executed.
        '''

        algoDict = {"singleRandom":self.step_single_random,
                        "singleClosest":self.step_single_closest,
                        "singleRandomSatisfyStop":self.step_single_randomSat_stop,
                        "singleRandomSatisfyContinue":self.step_single_randomSat_cont,
                        "singleClosestSatisfyStop":self.step_single_closestSat_stop,
                        "singleClosestSatisfyContinue":self.step_single_closestSat_cont,
                        "whitebatchRandom":self.step_whitebatch_random,
                        "batchRandom":self.step_batch_random,
                        "whitebatchRandomSatisfyStop":self.step_whitebatch_randomSat_stop,
                        "batchRandomSatisfyStop":self.step_batch_randomSat_stop,
                        "whitebatchRandomSatisfyContinue":self.step_whitebatch_randomSat_cont,
                        "batchRandomSatisfyContinue":self.step_batch_randomSat_cont,
                        "whitebatchClosest":self.step_whitebatch_closest,
                        "batchClosest":self.step_batch_closest,
                        "whitebatchClosestSatisfyStop":self.step_whitebatch_closestSat_stop,
                        "batchClosestSatisfyStop":self.step_batch_closestSat_stop,
                        "whitebatchClosestSatisfyContinue":self.step_whitebatch_closestSat_cont,
                        "batchClosestSatisfyContinue":self.step_batch_closestSat_cont}
        
        if assignAlgorithm in algoDict:
            stepfunction = algoDict[assignAlgorithm]
        else:
            raise ValueError(f"Wrong function name in run: '{assignAlgorithm}'.")
        i = 0

        Running = True
        while (i < iters) and Running:
            if (not self.unsatisfied):
                print(f"Converged to stable position with {assignAlgorithm} for board of p={self.pbound}.")
                break
            Running = stepfunction()
            i+=1
            # print(i)
        print("Done. i = ", i)
        return i
        
    def animate(self, total_frames=200, frame_jump=None, interval=0.5):
        '''
        After board has been run, plays frames in animation list.
        Arguments:
            total_frames: integer, approximate number of frames to play, higher causes greater jumps
                in animation list when scanning.
            frame_jump: integer, alternative to total_frames, assign exact number of frames to jump by.
            interval: float, effectively frames per second, corresponds to interval argument of FuncAnimation.
        '''

        fig = plt.figure()
        if frame_jump == None:
            frame_jump = len(self.animationList)//total_frames+1

        heatmap(self.animationList[0], cmap='vlag', xticklabels=False, yticklabels=False, cbar=False)

        animationList = self.animationList[::frame_jump]
        animationList.append(self.animationList[-1])
        time = len(animationList)

        def animate_step(i):
            fig.clear()
            heatmap(animationList[i], cmap='vlag', xticklabels=False, yticklabels=False, cbar=False)

        anim = animation.FuncAnimation(fig, animate_step, frames=time, repeat = True, interval=interval)
        plt.show()

        return anim
    def averagepval(self):
        '''
        Returns the average pval across all non-empty nodes.
        '''
        pvalcount = 0
        for row in self.board:
            for node in row:
                if node.color != 'white':
                    pvalcount += node.pval

        return pvalcount/(self.size**2 - len(self.whiteCells))

#### Example usage, creating and animating a batch random assignment board. #####
# randomboard = Board(50, 0.1, 0.5, 0.6, 1)
# randomboard.run(100, "batchRandom")
# anim = randomboard.animate()

##### Testing a range of values for the single closest satisfying with stops assigning algorithm. #####
##### Plots the linear dependence between pbound and the ending average pval ######
# testingRange = np.linspace(0, 1, 20)
# results = []
# for pval in testingRange:
#     currentboard = Board(50, 0.1, 0.5, pval, 10)
#     print(f"Finished {pval} in {currentboard.run(6000, "singleClosestSatisfyStop")} steps.")
#     currentpval = currentboard.averagepval()
#     print(f"Average pval = {currentpval}.")
#     results.append(currentpval)
# lineplot(x = testingRange, y = results)
# plt.show()