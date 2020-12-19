# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes with no warranty
#

# Functions converting the internal STG model to format accepted by Petrify

import p_types as t

def uniquify_transitions(model):
    '''
    Creates unique names for different transitions 
    that happens to have the same name of changing signal.

    Necessary for Petrify to cerrectly interpet the model.
    '''

    occurrence_counter = dict()

    for i in range(len(model.elements)):
        if type(model.elements[i]) is t.TreeTransition:
            tmp_name = model.elements[i].name

            if tmp_name in occurrence_counter:
                cnt = occurrence_counter[tmp_name]
                model.elements[i].name = tmp_name + '/' + str(cnt)
                occurrence_counter[tmp_name] = cnt + 1
            else:
                occurrence_counter[tmp_name] = 1


def to_petrify(model):
    uniquify_transitions(model)

    src = ''

    src += '.model %s\n' % model.meta.main
    src += '.inputs %s\n' % ' '.join(model.meta.inputs)
    src += '.outputs %s\n' % ' '.join(model.meta.outputs)
    src += '.graph\n'


    for elem in model.elements:
        line = elem.name
        for c in elem.children:
            line += ' %s' % c.name
        line += '\n'
        src += line

    markings = ''
    for elem in model.elements:
        if type(elem) is t.TreePlace:
            if elem.marking:
                markings += ' %s' % elem.name

    line = '.marking {%s }\n' % markings
    src += line
    src += '.end\n'

    return src

def save_file(model, src):
    filename = 'build/' + model.meta.main + '.g'
    with open(filename, 'w') as f:
        print('Saving to %s' %filename)
        f.write(src)

