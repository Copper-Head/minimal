# Created by Ilia Kurenkov
# This is a draft implementation of a chart minimalist parser as specified in 
# Harkema 2000 as well as Schieber et al 1995.

# A quick note on the implementation: i made a distinction between a node and 
# a phrase even though no such distinction was explicitly specified in Harkema.
# This was because I found it easier to have the phrase level encode which node
# was the head and which nodes were what I called "tail" (more formally, 
#     complements and specifiers)

###===== Imports ========================
###======================================
from __future__ import print_function
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

def is_selector(node):
    ''' check if phrase is a selector '''
    return ('=' in node['head'].features[-1])

def is_licensee(node, l):
    ''' check if a node contains licensee feature that matches a given licensor '''
    lice = node.features[-1].replace('-', '')
    if lice == l:
        return node
    else:
        return None

###========== Helper functions ===============
###===========================================
def concat_p(phrase1, phrase2):
    ''' concatinates indices of two phrases '''
    return (phrase1['head'].index[0], phrase2['head'].index[1])

def concat_n(node1, node2):
    ''' concatenates indices of two nodes '''
    return (node1.index[0], node2.index[1])

def cut_features(phrase):
    return Node(phrase['head'].index, phrase['head'].features[:-1])

def features_match(head, tail):
    ''' checks if feature of a selectee matches that of a selector '''
    if not is_selector(tail):   # first verify that selectee is not itself a selector
        selector = head['head'].features[-1].replace('=', '')
        selectee = tail['head'].features[-1]
        return (selector == selectee)
    return False

def try_merge(trigger, chart):
    ''' loops over the chart trying to merge its members with a given trigger'''
    return [merge(trigger, node) for node in chart]

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
    licensor_n = phrase['head']
    licensees = [x for x in (is_licensee(n, licensor) for n in phrase['tail']) if x]
    print('potential candidates for moving:')
    print_list(licensees)
    if len(licensees) == 1:
        moved = licensees[0]
        phrase['tail'].remove(moved)
        # moved.features.pop()
        # licensor_n.features.pop()
        if len(moved.features[:-1]) > 0:
            print('the moved phrase still has features left, cannot concatenate with head')
            newHead = cut_features(phrase)
            newMoved = Node(moved.index, moved.features[:-1])
            return make_phrase(newHead, phrase['tail'] + [newMoved])
        else:
            print('no more features on moved phrase, concatenating with head')
            newHead = Node(concat_n(licensor_n, moved), licensor_n.features[:-1])
            return make_phrase(newHead, phrase['tail'])
    else:
        print('more than one or no potential movers, operation cannot apply')
        return None

def merge(trigger, phrase):
    if is_selector(phrase) and features_match(phrase, trigger):
        head, tail = phrase, trigger
    elif is_selector(trigger) and features_match(trigger, phrase):
        head, tail = trigger, phrase
    else:
        # print('No merge possible, culprit:', phrase['head'])
        return None
    print('Selector -- Selectee:\n', head['head'], ' -- ', tail['head'])
    # head['head'].features.pop()
    # tail['head'].features.pop()
    if len(tail['head'].features[:-1]) > 0:
        print('Still some features left on tail, we cannot concatenate it with head')
        newTail = cut_features(tail)
        newHead = cut_features(head)
        tails = head['tail'] + [newTail] + tail['tail']
        return make_phrase(newHead, tails)
    else:
        print('No more features left on tail, contatenating with head')
        if is_lexical(head):
            print('Head is lexical/simple, merging tail as complement')
            newHead = Node(concat_p(head, tail), head['head'].features[:-1])
            newTail = tail['tail']
        else:
            print('Head is complex, merging tail as specifier')
            newHead = Node(concat_p(tail, head), head['head'].features[:-1])
            newTail = tail['tail'] + head['tail']
        return make_phrase(newHead, newTail)

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
            print("This trigger's a MERGER!")
            agenda.extend(try_merge(trigger, chart))
        # then we clean up our agenda
        agenda = [x for x in agenda if x]
        # add the item to the chart if it isn't already there
        if trigger not in chart:
            print('Trigger added to chart.', trigger)
            chart += [trigger]
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
    main()
