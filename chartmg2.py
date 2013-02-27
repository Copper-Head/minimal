# Created by Ilia Kurenkov
# This is a draft implementation of a chart minimalist parser as specified in 
# Harkema 2000 as well as Schieber et al 1995.

# This version incorporates the Adjoin and Scramble operations as defined by
# Frey and Gaertner 2002. The definitions for these operations are not yet
# complete. This file also features some restructuring and abstraction of the
# merge and to a lesser extent the move operations

# A quick note on the implementation: i made a distinction between a node and 
# a phrase even though no such distinction was explicitly specified in Harkema.
# This was because I found it easier to have the phrase level encode which node
# was the head and which nodes were what I called "tail" (more formally, 
#     complements and specifiers)

###===== Imports ========================
###======================================
from __future__ import print_function
import sys
from collections import namedtuple

###======= Set up ==========================
###=========================================
# create custom tuple class for nodes
Node = namedtuple('Node', ['index', 'features'])

def make_phrase(head, tail=[]):
    '''returns a phrase as a dictionary with keys 'head' and 'tail'
    This may be turned into a namedtuple later on for consistency'''
    return {'head': head, 'tail': tail}

###========== Boolean helper functions ==============
###==================================================
def reached_goal(chart, goals):
    '''check if any of the goals have been reached '''
    return len([x for x in goals if x  in chart]) > 0

def is_exhausted(agenda):
    ''' check if agenda is empty'''
    return len(agenda) == 0

def is_lexical(phrase):
    '''check if a phrase is lexical (only consists of a head)'''
    return len(phrase['tail']) == 0

def is_movable(phrase):
    ''' check if the move operation need be applied to a phrase'''
    return ('+' in phrase['head'].features[-1])

def is_selector(node, mark):
    ''' check if phrase is a selector '''
    return (mark in node['head'].features[-1])

def is_licensee(node, l):
    ''' check if a node contains licensee feature that matches a given licensor '''
    lice = node.features[-1].replace('-', '')
    if lice == l:
        return node
    else:
        return None

def features_match(head, tail, mark):
    ''' checks if feature of a selectee matches that of a selector '''
    if not is_selector(tail, mark):   # first verify that selectee is not itself a selector
        selector = head['head'].features[-1].replace(mark, '')
        selectee = tail['head'].features[-1]
        return (selector == selectee)
    return False

###========== Helper functions ===============
###===========================================
def concat(node1, node2):
    ''' concatinates indices of two nodes '''
    return (node1.index[0], node2.index[1])

def cut_features(phrase):
    return Node(phrase['head'].index, phrase['head'].features[:-1])

def establish_roles(trigger, phrase, mark):
    if is_selector(phrase, mark) and features_match(phrase, trigger, mark):
        return (phrase, trigger) 
    elif is_selector(trigger, mark) and features_match(trigger, phrase, mark):
        return (trigger, phrase)
    else:
        # print('No merge possible, culprit:', phrase['head'])
        return None

def print_list(iterable):
    '''custom print for lists'''
    if len(iterable) > 0:
        for i in iterable:
            print(i)
    else:
        print('EMPTY')

###============= Core functions ==============
###===========================================
def move(phrase):
    licensor = phrase['head'].features[-1].replace('+', '')
    licensor_node = phrase['head']
    curry_is_licensee = lambda x: is_licensee(x, licensor)
    licensees = filter(curry_is_licensee, phrase['tail'])
    print('potential candidates for moving:')
    print_list(licensees)
    if len(licensees) == 1:
        moved = licensees[0]
        phrase['tail'].remove(moved)
        newHead = cut_features(phrase)
        if len(moved.features[:-1]) > 0:
            print('the moved phrase still has features left, cannot concatenate with head')
            newMoved = Node(moved.index, moved.features[:-1])
            return make_phrase(newHead, phrase['tail'] + [newMoved])
        else:
            print('no more features on moved phrase, concatenating with head')
            newHead = Node(concat(newHead, moved), newHead.features)
            return make_phrase(newHead, phrase['tail'])
    else:
        print('more than one or no potential movers, operation cannot apply')
        return None

def merge(trigger, phrase):
    roles = establish_roles(trigger, phrase, '=')
    if not roles:
        return None
    else:
        head, tail = roles[0], roles[1]
   
    print('Selector -- Selectee:\n', head['head'], ' -- ', tail['head'])
    newTail = cut_features(tail) # type is Node, not phrase
    newHead = cut_features(head) # type is Node, not phrase
    if len(newTail.features) > 0:
        print('Still some features left on tail, we cannot concatenate it with head')
        #we combine the tail of head, tail with newTail in to get new tail list
        newTailS = head['tail'] + [newTail] + tail['tail']
    else:
        print('No more features left on tail, concatenating with head')
        newTailS = tail['tail'] # new tail will be whatever was in non-head 
        submerge = lambda n1, n2: Node(concat(n1, n2), newHead.features)
        if is_lexical(head):
            print('Head is lexical/simple, merging tail as complement')
            newHead = submerge(newHead, newTail)
        else:
            print('Head is complex, merging tail as specifier')
            newHead = submerge(newTail, newHead)
            newTailS += head['tail']
    return make_phrase(newHead, newTailS)

def adjoin(trigger, phrase):
    '''given a trigger and a phrase returns either None if adjoin is impossible
    or the result of adjoining one of the args with the other'''
    roles = establish_roles(trigger, phrase, '%')
    if not roles:
        return None
    else:
        head, adjunct = roles[1], roles[0]
    print('Head -- Adjunct:\n', head['head'], ' -- ', adjunct['head'])
    newAdjunct = cut_features(adjunct)
    newHead = head['head']
    if len(newAdjunct.features) > 0:
        print('Still some features left on adjunct, we cannot concatenate it with head')
        newTailS = head['tail'] + [newAdjunct] + adjunct['tail']
    else:
        print('No more features left on adjunct, concatenating with head')
        newTailS = head['tail'] + adjunct['tail']
        newHead = Node(concat(newAdjunct, newHead), newHead.features)
    return make_phrase(newHead, newTailS)
# testing adjoin
#x = make_phrase(Node((1,2), ['v','d']))
#y = make_phrase(Node((0,1), ['-f','%d']))
#z = make_phrase(Node((0,1), ['%d']))
#print(adjoin(x, y))
#print(adjoin(y, x))
#print(adjoin(z, x))


def recognize(agenda, goals, chart=[], counter=1):
    '''given a set of axioms represented by agenda and a set of goals
    represented by eponymous variable as well as an empty (to begin with)
    chart, returns True if any of the goals were achieved, False otherwise.
    The counter is there for printing purposes
    '''
    delim = "-"
    print('\n'+delim*80)
    print('Iteration #:', counter)
    # we start with the exic clause. if we've emptied our agenda we must check
    # if the goals were reached. the result of the check is returned
    if is_exhausted(agenda):
        print('We have exhausted the agenda (and maybe the computer too)')
        return reached_goal(chart, goals)
    # do the following until the agenda is exhausted
    else:
        print('There are still items on the agenda. Here they are:')
        print_list(agenda)
        print('Here is our current state of the chart:')
        print_list(chart)
        trigger = agenda.pop()
        print('\nOur trigger item is: ', trigger)
        # now we try to infer: we can either move...
        if is_movable(trigger):
            print("This trigger's a MOVER!")
            agenda.append(move(trigger))
        # or merge.
        else:
            print("This trigger's a MERGER or an ADJUNCT!") 
            curry_merge = lambda x: merge(trigger, x) #currying merge function 
            curry_adjoin = lambda x: adjoin(trigger, x) #currying adjoin function
            agenda.extend(map(curry_merge, chart))
            agenda.extend(map(curry_adjoin, chart))
        # then we clean up our agenda
        agenda = filter(None, agenda)
        # add the item to the chart if it isn't already there
        if trigger not in chart:
            print('Trigger added to chart.', trigger)
            chart.append(trigger)
        # proceed further in the derivation
        return recognize(agenda, goals, chart, counter+1)


###============ Testing ===================
###========================================
# testing merge and move
# x = make_phrase(Node((0,1), ['v','=d']))
# y = make_phrase(Node((1,2), ['-f','d']))
# t = make_phrase(Node((0,0), ['+f','=v']))
# es = merge(x, y)
# print move(merge(t, es))

# testing the whole program
def main():
    a = [
    Node((0, 0),['c','=i']),
    Node((0, 0), ['pred','=d','+k','=vt']),
    Node((0,1), ['-k','d']),
    Node((1, 1), ['c','=i']),
    Node((1, 1), ['pred','=d','+k','=vt']),
    Node((1,2), ['-v','vt','=d']),
    Node((2, 2), ['c','=i']),
    Node((2, 2), ['pred','=d','+k','=vt']),
    Node((2,3), ['i','+k','+v','=pred']),
    Node((3, 3), ['c','=i']),
    Node((3, 3), ['pred','=d','+k','=vt']),
    Node((3,4), ['-k','d']),
    Node((4, 4), ['c','=i']),
    Node((4, 4), ['pred','=d','+k','=vt']),
    ]
    g = [
    Node((0,4), ['c'])
    ]
    agenda = [make_phrase(x) for x in a]
    goals = [make_phrase(x) for x in g]
    print('Given the following Agenda:')
    print_list(agenda)
    print('And the following Goals:')
    print_list(goals)
    print('We have the following derivation:')
    print(recognize(agenda, goals))

if __name__ == '__main__':
    print('Running file:', sys.argv[0], '\n')
    main()
