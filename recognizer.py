# This program is free and subject to the conditions of the MIT license.
# If you care to read that, here's a link:
# http://opensource.org/licenses/MIT

#===================== IMPORTS --- SETUP --- GLOBAL VARS ======================
from __future__ import print_function
import os
import sys
import re
from collections import namedtuple

Tree = namedtuple('Tree', ['span', 'head', 'tail'])
features = namedtuple('features', ['checked', 'unchecked'])

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

#============================ Boolean Functions ===============================

def is_licensor(feat):
    return feat[0] == '+'

def is_selected(feat):
    return feat[0] != '+' and feat[0] != '='

def is_selector(feat):
    return feat[0] == '='

def is_head(phrase):
    feature = phrase.unchecked[0]
    return is_selector(feature) or is_licensor(feature)

def is_end_category(phrase):
    return phrase.unchecked[0] == 'c' and len(phrase.unchecked) == 1

#============================ Helper Functions ================================

def print_iter(iterable):
    '''custom print for lists'''
    if type(iterable) == list:
        retrieve = lambda x: x
    elif type(iterable) == dict:
        retrieve = lambda x: (x, iterable[x])
    else:
        raise Exception('Unsupported iterable type: {0}'.format(type(iterable)))
    if len(iterable) > 0:
        for i in iterable:
            print(retrieve(i))
    else:
        print('EMPTY')

def make_phrase(pos, features):
    pass

#def update(sorted_list, recognized):
    #for member in sorted_list:
        #if member[1] == 

def abort_due_to(word):
    return 'The lexicon does not have the word "{0}" in it, please enter \
something the lexicon will recognize or load a new lexicon'

def inherit_features(daughter):
    active = daughter.unchecked[0]
    checked = daughter.checked + [active]
    unchecked = daughter.unchecked[1:]
    return features(checked, unchecked)


#============================ Core Functions ==================================

def unmerge(feat, feat_type):
    if feat_type == 'selector':
        return features([], [feat.lstrip('=')])
    elif feat_type == 'selectee':
        return features([], ['=' + feat])

def unmove(feat):
    '''return an unmoved node'''
    pass

def scan(inpt, to_recognize):
    for priority in sorted(to_recognize, reverse=True):
        print('Top priority item on stack:', to_recognize[priority])
        print('Compared to the active item:', inpt)
        if inpt.unchecked[0] == to_recognize[priority][1].unchecked[0]:
            print('The item on the stack was recognized.')
            print('It will now serve as the active item...')
            if is_head(inpt):
                recognized = up(inpt)[0]
            else:
                recognized = to_recognize[priority][0]
            print('... after we remove it from the stack')
            del to_recognize[priority]
            print('Now we check the stack again, this time with our new item\n')
            return scan(recognized, to_recognize)
    print('No items on the stack matched this item or the stack was empty.')
    return (inpt, to_recognize)

def up(daughter, inherit=False):
    if inherit or is_head(daughter):
        return (inherit_features(daughter), daughter.unchecked[0])
    return (features([None], [None]), daughter.unchecked[0]) 

def down(feat):
    if is_selector(feat):
        return unmerge(feat, 'selector')
    elif is_selected(feat):
        return unmerge(feat, 'selectee')
    elif is_licensor(feat):
        return unmove(feat)
    else:
        raise Exception('there was a problem with this feature: {0}'.format(feat))

def parse(sent, lexicon):
    priority_counter = 0
    to_recognize = {}
    for word in sent:
        print('{}\nNew parsing cycle.'.format('#'*50))
        print('Contents of the stack:')
        print_iter(to_recognize)
        print('Reading input: "{}"'.format(word))
        if word not in lexicon:
            print('not found')
            abort_due_to(word)
        inpt = features([], lexicon[word])
        print('Found lexical entry:', inpt)
        #print scan(inpt, to_recognize)
        print('Scanning stack for matches with this active item')
        (match, to_recognize) = scan(inpt, to_recognize)
        current = match or inpt
        #print('recognized this phrase:', current)
        #print(current.unchecked[0] == 'c' )
        #print(len(current.unchecked) == 1)
        if not is_end_category(current):
            print('This is not the end yet!')
            (project_derive, feature) = up(current)
            expand_predict = down(feature)
            if project_derive and expand_predict:
                print ('Projection and prediction rules yield the following...')
                print('Semi-recognized mother:', project_derive)
                print('Unrecognized sister:', expand_predict)
                print('We add these items coupled together to the stack.')
                to_recognize[priority_counter] = (project_derive, expand_predict)
                priority_counter += 1
    print('It appears we have reached the end of the sentence.')
    print('Here are the contents of the stack:')
    print_iter(to_recognize)
    return len(to_recognize) == 0

#================================= __MAIN__ ===================================
def main(demo=True):
    print('For now this is just a demo.')
    lex = parse_axiom_file('test.lex')['lex']
    print('We have the following Lexicon:')
    print_iter(lex)
    if demo:
        print('Is the sentence "mary eats meat" grammatical?')
        print(parse(['start'] + SENT.split(), lex))
    else:
        sent_to_parse = raw_input('Please enter some words to parse\n').split()
        print('Parser, do you recognize this sentence?')
        print(parse(sent_to_parse, lex))

#------------------------------------------------------------------------------
if __name__ == '__main__':
    main()

