# This program is free and subject to the conditions of the MIT license.
# If you care to read that, here's a link:
# http://opensource.org/licenses/MIT

#===================== IMPORTS --- SETUP --- GLOBAL VARS ======================
from __future__ import print_function # for python 3.x printing 
#import os
#import sys
#import re
from collections import namedtuple
# try to import numpy and matplotlib, if imports fail, no plots will be drawn
try:
    import numpy as np # needed to create Axes for plots 
    numpy_imported = True
except ImportError:
    numpy_imported = False
try:
    import matplotlib.pyplot as plt # needed to plot stuff 
    plotting_imported = True
except ImportError:
    plotting_imported = False

tree = namedtuple('tree', ['head', 'features', 'tree_type'])
pair = namedtuple('pair', ['part_confirmed', 'unconfirmed'])
#features = namedtuple('features', ['checked', 'unchecked'])

SENT = 'mary eats meat' # sentence for the demo 

###============ I/O Helper Functions ================

def parse_axiom_file(fileName):
    ''' This function parses an axiom file.
    It assumes sane entries for the axioms so these are not checked for validity.
    '''
    def has_comment(line):
        return ('#' in line)

    def is_flag(line):
        return ''.join(line).startswith('!')

    def determine_state(line):
        if 'LEXICAL' in line:
            return 'lex'
        elif 'GOALS' in line:
            return 'goals'
        elif 'NON-LEXICAL' in line:
            return 'non-lex'
        else:
            raise Exception('Unkown flag', line)
    
    # after some helper functions let's define our output variable
    d = {
    'lex': {},      # lexical axioms are special
    'goals': [],
    'non-lex': [],
    }
    # set state to non-lex by default
    state = 'non-lex'
    # now we open the file
    with open(fileName) as file:
        for line in file:
            if has_comment(line):
                relevantLine = line[:line.index('#')].split()
            else:
                relevantLine = line.split()
            empty_line = len(relevantLine) == 0
            # check if line contains a flag
            if not empty_line and is_flag(relevantLine):
                state = determine_state(relevantLine)
                # now check if entry is lexical
            elif not empty_line and state == 'lex':
                d[state][relevantLine[0]] = relevantLine[1:]
            elif not empty_line:
                d[state].append(relevantLine)
    return d

def find_lex_axioms(sent, d):
    '''Function finds lexical axioms present in sent and loaded in our grammar.
    If one word is not found, raises Exception asking user to reenter the word.
    '''
    lexAxioms = []
    for indx in xrange(len(sent)):
        if sent[indx] in d:
            lexAxioms.append(((indx, indx+1), d[sent[indx]]))
        else:
            raise Exception(sent[indx])
    return [Node(x[0], x[1]) for x in lexAxioms]

def plot_stack(sent, stack_sizes):
    '''plots size of stack change over tokens processed'''
    # set plot title and y-axis label
    plt.title('Stack Size over Tokens Traversed')
    plt.ylabel('Stack Size')
    ind = np.arange(len(sent))
    #ind = range(len(sent))
    width = 0.4
    #generate plot
    bars = plt.bar(ind, stack_sizes, width, color='g')
    #set ticks for both axes
    plt.xticks(ind+width/2, sent)
    plt.yticks(range(0,max(stack_sizes)+2,1))
    #draw the plot
    plt.show()

#============================ Boolean Functions ===============================

def is_licensor(feat):
    '''checks if feat is a licensor'''
    return feat[0] == '+'

def is_selected(feat):
    '''checks if feature is a base that is being selected'''
    return feat[0] != '+' and feat[0] != '='

def is_selector(feat):
    '''checks if feature is selector'''
    return feat[0] == '='

def is_head(phrase):
    '''checks if phrase is a head'''
    feature = phrase[0]
    return is_selector(feature) or is_licensor(feature)

def is_movable(item):
    return '+' in item.head[0]

def is_end_category(phrase):
    '''checks if phrase is the distinguished or end category'''
    return phrase.head[0] == 'c' and len(phrase.head) == 1

#============================ Helper Functions ================================

def match(item1, item2):
    return (item1.head[0] == item2.head[0] and 
            (item2.tree_type == 'either' 
                or item1.tree_type == item2.tree_type))

def print_iter(iterable):
    '''custom print for iterables such as lists and dictionaries'''
    if type(iterable) == list: # if we have a list 
        retrieve = lambda x: x
    elif type(iterable) == dict: # if we have a dictionary 
        retrieve = lambda x: (x, iterable[x])
    else: # in case it is neither 
        raise Exception('Unsupported iterable type: {0}'.format(type(iterable)))
    if len(iterable) > 0:
        for i in iterable:
            print(retrieve(i))
    else:
        print('EMPTY')

def abort_due_to(word):
    return 'The lexicon does not have the word "{0}" in it, please enter \
something the lexicon will recognize or load a new lexicon'

def project_predict(feats):
    print(feats)
    return pair(up(feats), down(feats[0]))

#============================ Core Functions ==================================

def unmerge(feat, feat_type):
    '''Depending on whether the feat_type is selector or selectee returns a
    projected (yet unrecognized) node that will be then added to the stack'''
    if feat_type == 'selectee':
        return tree([feat.lstrip('=')], [], 'either')
    elif feat_type == 'selector':
        return tree(['=' + feat], [], 'complex')

def unmove(item):
    '''return an unmoved node'''
    f = '-' + item.head[0].strip('+')
    if item.features.count(f) == 1:
        item.features.remove(f)
        return tree(item.head[1:], item.features, 'complex')

def scan(inpt, to_recognize):
    ''' Compares inpt to every member of to_recognize.
    inpt : node that was either read in or passed by previous iterations of scan()
    to_recognize : stack of unrecognized nodes
    '''
    for priority, pair in sorted(to_recognize, reverse=True):
        print('Top priority item on stack:', pair)
        print('Compared to the active item:', inpt)
        if match(inpt, pair.unconfirmed):
            print('The item on the stack was recognized.')
            print('It will now serve as the active item...')
            if is_head(inpt.head):
                recognized = tree(inpt.head[1:], inpt.features, 'complex')
                print(recognized)
            else:
                recognized = pair.part_confirmed
            print('... after we remove it from the stack')
            if priority != 0: # keep null items on stack 
                to_recognize.remove((priority, pair))
            print('Now we check the stack again, this time with our new item\n')
            return scan(recognized, to_recognize)
    print('No items on the stack matched this item or the stack was empty.')
    return (inpt, to_recognize)

def up(feats):
    '''Project a semi-recognized mother node from daughter.
    if inherit=True or daughter is determined to be a head, the constructed
        mother will inherit the features of the daughter, otherwise the
        features will be set to None and inherited from the sister node of the
        current daughter one.
        '''
    if is_head(feats):
        return tree(feats[1:], [], 'complex')
    return tree([None], [], 'complex')

def down(feat):
    '''Determines what operation to use to construct a projected unrecognized
    node based on the feature feat. '''
    print(feat)
    if is_selector(feat):
        return unmerge(feat, 'selectee')
    elif is_selected(feat):
        return unmerge(feat, 'selector')
    else:
        raise Exception('there was a problem with this feature: {0}'.format(feat))

def parse(sent, lexicon, null_cats):
    priority_counter = 1
    stack_sizes = [0]
    to_recognize = [(0, project_predict(item)) for item in null_cats]
    non_lex = len(to_recognize)
    for word in sent:
        print('{}\nNew parsing cycle.'.format('#'*50))
        print('Contents of the stack:')
        print_iter(to_recognize)
        print('Reading input: "{}"'.format(word))
        if word not in lexicon:
            print('not found')
            abort_due_to(word)
        inpt = tree(lexicon[word], [], 'simple')
        print('Found lexical entry:', inpt)
        print('Scanning stack for matches with this active item')
        (current, to_recognize) = scan(inpt, to_recognize)
        if not is_end_category(current):
            print('This is not the end yet!')
            if is_movable(current):
                current = unmove(current)
            to_recognize.append((priority_counter, project_predict(current.head)))
            priority_counter += 1
            #if project_derive and expand_predict:
                #print ('Projection and prediction rules yield the following...')
                #print('Semi-recognized mother:', project_derive)
                #print('Unrecognized sister:', expand_predict)
                #print('We add these items coupled together to the stack.')
        stack_sizes.append(max((len(to_recognize)-non_lex),0))
    print('It appears we have reached the end of the sentence.')
    print('Here are the contents of the stack:')
    print_iter(to_recognize)
    stack_sizes.append(max((len(to_recognize)-non_lex),0))
    if numpy_imported and plotting_imported:
        # plots cut off at the last token for some reason, so we add a dummy token
        # to the sent list and a dummy value to the stack_sizes list
        sent = [''] + sent + ['']
        plot_stack(sent, stack_sizes)
    return len([x for x, y in to_recognize if x > 0]) == 0

#================================= __MAIN__ ===================================
def main(demo=True):
    print('For now this is just a demo.')
    axiom_file = parse_axiom_file('test.lex')
    lex = axiom_file['lex']
    n_cats = axiom_file['non-lex']
    print('We have the following Lexicon:')
    print_iter(lex)
    print('And the following non-lexical categories:')
    print_iter(n_cats)
    if demo:
        print('Is the sentence "mary eats meat" grammatical?')
        #print(parse(['start'] + SENT.split(), lex))
        print(parse(SENT.split(), lex, n_cats))
    else:
        sent_to_parse = raw_input('Please enter some words to parse\n').split()
        print('Parser, do you recognize this sentence?')
        print(parse(sent_to_parse, lex, n_cats))

#------------------------------------------------------------------------------
if __name__ == '__main__':
    main()

