# This program is free and subject to the conditions of the MIT license.
# If you care to read that, here's a link:
# http://opensource.org/licenses/MIT

#===================== IMPORTS --- SETUP --- GLOBAL VARS ======================
from __future__ import print_function # for python 3.x printing 
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

def plot_stack(sent, stack_sizes):
    '''plots size of stack over tokens processed'''
    # set plot title and y-axis label
    plt.title('Stack Size over Tokens Traversed')
    plt.ylabel('Stack Size')
    ind = np.arange(len(sent))
    #ind = range(len(sent))
    width = 0.4
    #generate plot
    bars = plt.bar(ind, stack_sizes, width, color='g')
    #set ticks for both axes
    #plt.xticks(ind+width/2, sent)
    plt.xticks(ind,sent)
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
    feature = phrase.head[0]
    return is_selector(feature) or is_licensor(feature)

def is_movable(item):
    return '+' in item.head[0]

def is_end_category(phrase, goals):
    '''checks if phrase is the distinguished or end category'''
    return (phrase.head[0] in goals) and (len(phrase.head) == 1)

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

def project_predict(item):
    return pair(up(item), unmerge(item))

#============================ Core Functions ==================================

def unmerge(item):
    '''Depending on whether the feat_type is selector or selectee returns a
    projected (yet unrecognized) node that will be then added to the stack'''
    feat = item.head[0]
    if is_selector(feat):
        sister = tree([feat.lstrip('=')], [], 'either')
    elif is_selected(feat):
        sister = tree(['=' + feat], [], 'complex')
    return sister

def unmove(item):
    '''return an unmoved node'''
    f = '-' + item.head[0].strip('+')
    if item.features.count(f) == 1:
        item.features.remove(f)
        return tree(item.head[1:], item.features, 'complex')
    raise Exception('Move impossible! \nHere is the culprit: {}'.format(item))

def up(item):
    '''Project a semi-recognized mother node from daughter.
    if inherit=True or daughter is determined to be a head, the constructed
        mother will inherit the features of the daughter, otherwise the
        features will be set to None and inherited from the sister node of the
        current daughter one.
        '''
    xtract_licensees = item.features + [f for f in item.head if "-" in f]
    if is_head(item):
        return tree(item.head[1:], xtract_licensees, 'complex')
    return tree([None], xtract_licensees, 'complex')

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
            new_licensees = inpt.features + pair.part_confirmed.features
            if is_head(inpt):
                recognized = tree(inpt.head[1:], new_licensees, 'complex')
            else:
                new_head = pair.part_confirmed.head
                recognized = tree(new_head, new_licensees, "complex")
            print('... after we remove it from the stack')
            if priority != 0: # keep null items on stack 
                to_recognize.remove((priority, pair))
            print('Now we check the stack again, this time with our new item\n')
            return scan(recognized, to_recognize)
    print('No items on the stack matched this item or the stack was empty.')
    return (inpt, to_recognize)

def parse(sent, lexicon, null_cats, goals):
    priority_counter = 1
    stack_sizes = [0]
    to_recognize = [(0, project_predict(item)) for item in 
           (tree(x, [], "simple") for x in null_cats)]
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
        if is_movable(current):
            print('unmoving...')
            current = unmove(current)
        if not is_end_category(current, goals):
            print('This is not the end yet!')
            to_recognize.append((priority_counter, project_predict(current)))
            priority_counter += 1
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
    return sum(1 for x, y in to_recognize if x > 0) == 0

#================================= __MAIN__ ===================================
def main(sent, demo=True):
    print('For now this is just a demo.')
    axiom_file = parse_axiom_file('test.lex')
    lex = axiom_file['lex']
    n_cats = axiom_file['non-lex']
    gols = [g[0] for g in axiom_file['goals']]
    print('We have the following Lexicon:')
    print_iter(lex)
    print('And the following non-lexical categories:')
    print_iter(n_cats)
    print('And the following goals:')
    print_iter(gols)
    if demo:
        print('Is the sentence "{0}" grammatical?'.format(sent))
        print(parse(sent.split(), lex, n_cats, gols))
    else:
        sent_to_parse = raw_input('Please enter some words to parse\n').split()
        print('Parser, do you recognize this sentence?')
        print(parse(sent_to_parse, lex, n_cats))

#------------------------------------------------------------------------------
if __name__ == '__main__':
    # sentences for the demo 
    #sent = 'mary eats meat' 
    sent = "maria will speak nahuatl"
    main(sent)

