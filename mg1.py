# Umass Amherst Linguistics
# author: Ilia Kurenkov
# First attempt at modelling a minimalist Grammar

# This is just a demonstration of a rudimentary version of the MG formalism in
# action

# Known Issues:
# slightly inaccurate representation of the lexicon
# no support for CAPITALIZED licensors
# during move, the program doesn't check if there are multiple phrases with
# unchecked licensee feature. it simply returns the first such phrases it finds
# and raises an error if none are present

# for convenience imported the sub function to make professing features simpler
from re import sub

# Because I wasn't worried too much about implementing a retrieval algorithm
# for this toy example, I decided to use the lexicon as a stack and feed my
# derivation function items one by one. Thus in this case in order for the
# derivation not to crash it is important to store items in the lexicon in a
# strict order. I do not forsee this being the case in future implementations
# as much, especially once we finally figure out which algorithm to use for
# retrieving entries.
# All lexical entries also have the head index. This is done in part to
# simplify tree traversal and finding heads
# and in part to reflect one of the properties of MGs,
# namely that every head is a leaf and every leaf is its own head
# NB
# Keep in mind that "lexical" expressions consist of an index and a feature
# bundle, whereas derived expressions have in addition to that a second feature
# bundle. This distinction in length will be used several times in the
# program.

LEX = [
    (1, ('=t', 'c')),
    (1, ('=v', '+case', 't')),
    (1, ('d', '-case', 'maria')),
    (1, ('=d', '+case', '=d', 'v', '(speaks)', '/speaks/')),
    (1, ('n', '(language)', '/language/')),
    (1, ('=n', 'd', '-case', '(every)', '/every/')),
    ]

# utility regular expression to strip signs off licensors and selectors
exps = '[=+-]'

# I found it useful to define a custom exception for this case. Dunno to what
# extent it will be useful in the future.
class ParsingError(Exception):
    """a custom error to raise when parsing stalls"""
    def __init__(self, message):
        Exception.__init__(self, message)
# function for finding a head of a phrase
def head(phrase):
    ''' given a phrase returns its head '''
    h = phrase[phrase[0]]
    if len(phrase) == 2:  # testing if expression lexical
        return phrase #if yes, returning expression 
    else: #otherwise, recursing deeper 
        return head(h)
# testing head = works
# print head((1, ('d', '-case', '(maria)', '/maria/')))
#t = (2, (1, ('-case', '(maria)', '/maria/')), (1, ('(reads)', '/reads/')))
# print head(t)

# now a function to "check off" features
def del_feat(phrase, f):
    '''given a phrase and a feature returns the phrase with the feature
    removed. '''
    if len(phrase) == 2 and phrase[1][0] == f:
        return (phrase[0], phrase[1][1:])
    elif len(phrase) == 2 and (phrase[1][0] != f):
        # not sure this clause is needed actuallf
        raise ParsingError('matching feature not found: {0}, {1}'.format(phrase, f))
    else:
        if phrase[0] == 1:
            return (phrase[0], del_feat(phrase[1], f), phrase[2])
        elif phrase[0] == 2:
            return (phrase[0], phrase[1], del_feat(phrase[2], f))
        else:
            raise ParsingError('this phrase contains no head index: {}'.format(phrase))
# testing del_feat: works
#t = (1, ('d', '-case', '(man)', '/man/'))
# print del_feat(t, 'd')
#t = (2, (1, ('the')), (1, ('d', '-case', '(man)', '/man/')))
# print del_feat(t, 'd')
# print del_feat(t, 'd')

# a function for the merge operation
def merge(h, h_phrase, nonh):
    x = sub(exps,'', h[1][0])
    if h == h_phrase:      #if head is lexical
        return (1, del_feat(h,h[1][0]), del_feat(nonh,x))
    else:                   #if head already has complement
        return (2, del_feat(nonh,x), del_feat(h_phrase,h[1][0]))
# testing merge: works
# th = (1, ('=d', 'laughed'))
# print merge(th, th, t)

# and one for move
def move(tree, feature):
    def search(tree, f):
        '''helper function that given a tree and a feature, finds the first
        node that has said feature'''
        if head(tree)[1][0] == '-'+f: 
            # Found a match!!
            return tree
        elif head(tree)[1][0] != '-'+f and len(tree) == 3:
            # more searching...
            return search(tree[3-tree[0]], f)
        else:
            pass

    def modify(tree, target):
        if tree == target:
            return (1, ())
        elif tree != target and len(tree) == 2:
            return tree
        else:
            return (tree[0], modify(tree[1], target), modify(tree[2], target))

    matches = search(tree, feature)
    if not matches:
        raise ParsingError('no licensee found :(')
    else:
        # construct the phrase
        return (2, del_feat(matches, '-'+feature), del_feat(modify(tree, matches), '+'+feature))

# testing move: works
#t = (1, (1, ('+case', 'laughed')), (2, (1, ('the')), (1, ('-case', '(man)', '/man/'))))
# print move(t, 'case')


def derive(lexicon, progress=None):
    ''' given a lexicon, derives a sentence structure. 
    The use of lexicon in this case is somewhat differently than is intended in
    a classical MG. This is because I did not include a model of an "oracle" or
    some such algorithm that would retrieve items from the Lex.'''
    if len(lexicon) == 0:
        return progress
    else:
        print 'progress', progress
        if not progress:
            progress = lexicon.pop()
        progress_head = head(progress)
        # print 'next', next
        print 'old head', progress_head
        if '+' in progress_head[1][0]:
            progress = move(progress, sub(exps, '', progress_head[1][0]))
        else:
            next = lexicon.pop()
            if '=' in progress_head[1][0]:
                progress = merge(progress_head, progress, next)
            elif '=' in next[1][0]:
                progress = merge(next, next, progress)
            else:
                raise ParsingError('no potential heads detected')
        return derive(lexicon, progress)
#testing derive: (this should work...)
print derive(LEX)
