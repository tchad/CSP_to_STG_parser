# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes with no warranty
#

# Utility functions

import p_types as t 

def extract_block_subarray(idx, arr):
    '''
    Extracts set of tokens enclosed by outermost square brackets.

    Takes into account open/close count.
    '''

    opening = arr[idx]
    closing = ''

    if opening == '[':
        closing = ']'
    elif opening == '(':
        closing = ')'
    elif opening == '*[':
        opening = '['
        closing = ']'
    else:
        raise Exception("Unknown block opening operator %s" % opening)

    ret = []
    i = idx+1
    last = len(arr)
    cnt = 1

    while cnt > 0 and i < last:
        tmp = arr[i]
        if tmp == opening:
            cnt = cnt + 1
        elif tmp == closing:
            cnt = cnt - 1

        ret = ret + [tmp]

        i = i + 1

    if cnt != 0:
        raise Exception("Syntax error, missing closing operator")

    return (i, ret[:-1])

def get_src(label, model):
    '''
    Seraches by name and returns tokens of a CSP fragment.
    '''

    fragment_src = None

    for f in model.code_fragments:
        if f.label == label:
            fragment_src = f.src
            break

    if fragment_src == None:
        raise Exception("Could not find the main entry: %s" % main_label)
    
    ret = fragment_src.split(' ')
    while '' in ret:
        ret.remove('')

    return ret

def gen_place_label(model):
    '''
    Autogenerates a new name for an STG place while avoiding
    name collision"
    '''

    i = -1
    label = ''
    done = False

    while done == False:
        i = i + 1
        label = 'P%d' % i
        done = True

        for l in model.meta.explicit_place:
            if label == l:
                done = False

        if done == True:
            for l in model.elements:
                if (type(l) is t.TreePlace) and (label == l.name):
                    done = False

    return label

def is_explicit_place(model, token):
    if type(token) is t.TreePlace:
        n = token.name
    else:
        n = token

    for place in model.meta.explicit_place:
        if n == place:
            return True

    return False

def get_place(model, label):
    for elem in model.elements:
        if type(elem) is t.TreePlace:
            if elem.name == label:
                return elem

    return None

def is_transition(model, token):

    for tran in model.meta.inputs:
        if token == (tran + r"+") or token == (tran + r"-"):
            return True

    for tran in model.meta.outputs:
        if token == (tran + r"+") or token == (tran + r"-"):
            return True
            
    return False

def is_fragment(model, token):
    for frag in model.meta.fragments:
        if token == frag:
            return True

    return False

def elem_desc(elem):
    classname = '%s' % type(elem)
    class_desc = ''

    if type(elem) is t.TreePlace:
        if elem.marking:
            marking = r'*'
        else:
            marking = r' '

        class_desc = 'PLC: %s[%s]' % (elem.name, marking)
    elif type(elem) is t.TreeTransition:
        class_desc = 'TRN: %s' % elem.name
    elif type(elem) is t.TreeFragment:
        if elem.label == '':
            content = elem.src
        else:
            content = elem.label

        class_desc = 'FRG: %s' % content
    elif type(elem) is t.TreeLoopFragmentBegin:
        class_desc = 'LPB'
    elif type(elem) is t.TreeLoopFragmentEnd:
        class_desc = 'LPE'
    else:
        class_desc = 'UKN'

    #temporary
    classname = ''


    ret = '%s' % class_desc
    return ret

def have_all(data_set, names, exact = False):
    #checks if all given names appear in the data set (allows superset if exact=false)

    dataset_names = [ e.name for e in data_set]

    if (exact == True) and (len(dataset_names) != len(names)):
        return False

    for n in names:
        if n not in dataset_names:
            return False;

    return True;

def get_parents(model, elem):
    ret = []
    for e in model.elements:
        if elem in e.children:
            ret += [e]

    return ret

def match_strictly(model, inputs, outputs, elem_type, search_set=None):
    ret = []

    if search_set:
        data_set = search_set
    else:
        data_set = model.elements

    for elem in data_set:
        if type(elem) is not elem_type:
            continue

        if len(outputs) != len(elem.children):
            continue

        parents = get_parents(model, elem)

        if len(inputs) != len(parents):
            continue

        have_all_outputs = have_all(elem.children, outputs)
        have_all_inputs = have_all(parents, inputs)

        if (not have_all_outputs) or (not have_all_inputs):
            continue

        ret += [elem]

    return ret

def match_outputs(model, outputs, elem_type, search_set=None):
    ret = []

    if search_set:
        data_set = search_set
    else:
        data_set = model.elements

    for elem in data_set:
        if type(elem) is not elem_type:
            continue

        if len(outputs) != len(elem.children):
            continue

        if not have_all(elem.children, outputs):
            continue

        ret += [elem]

    return ret

def match_inputs(model, inputs, elem_type, search_set=None):
    ret = []

    if search_set:
        data_set = search_set
    else:
        data_set = model.elements

    for elem in data_set:
        if type(elem) is not elem_type:
            continue

        parents = get_parents(model, elem)

        if len(inputs) != len(parents):
            continue

        if not have_all(parents, inputs):
            continue

        ret += [elem]

    return ret

def match_inputs_relaxed(model, inputs, elem_type, search_set=None):
    #this version does not assume strict match in inputs
    #having all inputs required and potentially some additional ones 
    #satisfies the condition
    ret = []

    if search_set:
        data_set = search_set
    else:
        data_set = model.elements

    for elem in data_set:
        if type(elem) is not elem_type:
            continue

        parents = get_parents(model, elem)

        if not have_all(parents, inputs):
            continue

        ret += [elem]

    return ret

def match_outputs_relaxed(model, outputs, elem_type, search_set=None):
    #this version does not assume strict match in outputs
    #having all outputs required and potentially some additional ones 
    #satisfies the condition
    ret = []

    if search_set:
        data_set = search_set
    else:
        data_set = model.elements

    for elem in data_set:
        if type(elem) is not elem_type:
            continue

        if not have_all(elem.children, outputs):
            continue

        ret += [elem]

    return ret

def find_transition_one_to_one(model, src_label, dst_label):
    ret = []
    sources = match_outputs_relaxed(model, [dst_label], t.TreeTransition)
    destinations = match_inputs(model, [src_label], t.TreeTransition)

    for s in sources:
        for d in destinations:
            parents = get_parents(model, d)
            cnd1 = False
            cnd2 = False

            if s in parents:
                cnd1 = True

            if d in s.children:
                cnd2 = True

            ret += [(s,d)]

    return ret


def print_graph(model):
    for e in model.elements:
        print(elem_desc(e))
        for c in e.children:
            print(' |--%s' % elem_desc(c))


def print_graph2(model):
    for e in model.elements:
        out = elem_desc(e) + " -> "
        for c in e.children:
            out = out + ' (' + elem_desc(c) + ')'

        print(out)

def loop_place_equiv(p1, p2):
    '''compares two loop place specs regardless of order of transitions in array'''

    if len(p1.input) != len(p2.input):
        return False

    if len(p1.output) != len(p2.output):
        return False

    for e in p1.input:
        if e not in p2.input:
            return False;

    for e in p1.output:
        if e not in p2.output:
            return False;

    return True


