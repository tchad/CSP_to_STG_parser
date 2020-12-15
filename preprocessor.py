# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes witn no warranty
#

# The CSP source parser to token representation

import re
import regex
import p_types as t

def load_raw(model, filename):
    with open(filename) as f:

        #read entire file into string
        model.raw_src = f.read();

        #replace any \n and \t and multiple spaces with single space 
        tmp = re.sub('\s+', ' ', model.raw_src).strip()

        #divide the sources into header and code using endinterface beaker
        exp = re.compile(regex.HEADER_CODE_BREAK)
        m = exp.match(tmp)

        if m == None:
            raise Exception("Failed to recognize the base interface/code structure")

        model.interface_raw_src = m.group(1)
        model.code_raw_src = m.group(2)

def load(filename):
    model = t.Model()
    load_raw(model, filename)

    return model

def process_meta(model):
    src = model.interface_raw_src
    meta = t.Meta()

    print("Reading header metadata")

    if regex.module_controller.search(src):
        print("Identified module controller")
        meta.model_type = t.MetaModelType.CONTROLLER
    elif regex.module_behav.search(src):
        print("Identified module behav")
        meta.model_type = t.MetaModelType.BEHAV
    else:
        print("Undefined module type")
        meta.model_type = t.MetaModelType.UNDEFINED


    match_main = regex.main.search(src)
    if match_main:
        print("Found main handler: %s" % match_main.group(1))
        meta.main = match_main.group(1)
        
    match_fragment = regex.fragment.findall(src)
    if match_fragment:
        print('Found fragments: %s' % ', '.join(match_fragment))
        meta.fragments = match_fragment

    match_inputs = regex.inputs.findall(src)
    if match_inputs:
        #FIXME!!! one line expected
        print('Found inputs: %s' % match_inputs[0])
        meta.inputs = match_inputs[0].split(' ')

    match_outputs = regex.outputs.findall(src)
    if match_outputs:
        #FIXME!!! one line expected
        print('Found outputs: %s' % match_outputs[0])
        meta.outputs = match_outputs[0].split(' ')

    match_marking = regex.marking.finditer(src)
    for m in match_marking:
        place = t.MetaPlace()
        place.input = m.group(1).split(' ')
        place.output = m.group(2).split(' ')
        print('Found marking: %s -> %s' %(' '.join(place.input), ' '.join(place.output)))
        meta.markings = [place] + meta.markings

    match_loop_place = regex.loop_place.finditer(src)
    for m in match_loop_place:
        place = t.MetaPlace()
        place.input = m.group(1).split(' ')
        place.output = m.group(2).split(' ')
        print('Found loop_place: %s -> %s' %(' '.join(place.input), ' '.join(place.output)))
        meta.loop_place = [place] + meta.loop_place

    match_explicit_place = regex.explicit_place.findall(src)
    if match_explicit_place:
        print('Found explicit defined places: %s' % ', '.join(match_explicit_place))
        meta.explicit_place = match_explicit_place

    model.meta = meta
    

def preprocess_code(model):
    src =  model.code_raw_src
    labels = [model.meta.main]

    for l in model.meta.fragments:
        labels = labels + [l]

    fragments = split_fragments(labels, src)

    for f in fragments:
        code_fragment = t.CodeFragment(f[0], normalize_syntax(f[1]))
        model.code_fragments += [code_fragment]


def split_fragments(labels, src):
    matches = []
 
    for l in labels:
        match = re.search(regex.label_fix(l)+':', src);

        if match == None:
            raise Exception("Label %s not found" % l)

        matches = matches + [match]

    matches.sort(key=lambda m : m.span()[1])

    fragments = []

    for i in range(len(matches)):
        label = matches[i].group()[:-1]
        fragment_src = ''

        begin = matches[i].span()[1]+1

        if i == (len(matches)-1):
            #special case last label
            fragment_src = src[begin:]
        else:
            end = matches[i+1].span()[0]
            fragment_src = src[begin:end]

        fragments = fragments + [(label, fragment_src)]

    return fragments


def normalize_syntax(src):
    src = re.sub(regex.TEMPL_SQR_BR_L, regex.SYNTAX_SQR_BR_L, src);
    src = re.sub(regex.TEMPL_SQR_BR_R, regex.SYNTAX_SQR_BR_R, src);
    src = re.sub(regex.TEMPL_CONFUSION, regex.SYNTAX_CONFUSION, src);
    src = re.sub(regex.TEMPL_PAR_L, regex.SYNTAX_PAR_L, src);
    src = re.sub(regex.TEMPL_PAR_R, regex.SYNTAX_PAR_R, src);
    src = re.sub(regex.TEMPL_CONFUSION_ARB, regex.SYNTAX_CONFUSION_ARB, src);
    src = re.sub(regex.TEMPL_ACT, regex.SYNTAX_ACT, src);
    src = re.sub(regex.TEMPL_SEQ, regex.SYNTAX_SEQ, src);
    src = re.sub(regex.TEMPL_PARALLEL, regex.SYNTAX_PARALLEL, src);
    src = re.sub(regex.TEMPL_LOOP, regex.SYNTAX_LOOP, src);
    src = re.sub(regex.TEMPL_EPL, regex.SYNTAX_EPL, src);
    src = re.sub(regex.TEMPL_SEP, regex.SYNTAX_SEP, src);

    #remove multiple spaces
    src = re.sub('\s+', ' ', src)

    return src

def process(model):
    process_meta(model)
    preprocess_code(model)
