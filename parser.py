# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes witn no warranty
#

#Main parser

import re
import p_types as t 
import util
import syntax
from enum import Enum

def gen_tree(model):
    #main function that generates the stg graph


    #instantiate first tree element containing main procedure
    entry = t.TreeFragment()
    entry.label = model.meta.main

    model.elements = [entry]
    model.entry = entry

    finished = False

    print('Parsing code')
    #loop until all TreeFragment objects are parsed
    while finished == False:
        finished = True
        for e in model.elements:
            if type(e) is t.TreeFragment:
                finished = False
                parse_tree_fragment(model, e)
                break

    #clear up unnecesarry or redundant places
    remove_redundant_places(model)

    #apply loop if present
    apply_loop_places(model)

    #clear up unnecesarry or redundant places( 2nd pass)
    remove_redundant_places(model)

    #insert markings
    apply_markings(model)

    print('Parsed tree:')
    util.print_graph2(model)
    print('\n\n')

    print('Parsing finished')

class SegmentParseStatus(Enum):
    DEFAULT = 0
    

def parse_tree_fragment(model, fragment):
    #parse a single source fragment present in the tree
    #all source fragments are eventually decomposed into set of transitions and places

    if len(fragment.src) > 0:
        #if source code is present parse

        head = []
        tail = []

        status = parse_segment(model, head, tail, fragment.src)

        #replace fragment connections
        #swap source fragment with processed fragment including all
        #parent-children connections

        model.elements.remove(fragment)
        for p in model.elements:
            #remove any children connections pointing to the processed fragment
            if fragment in p.children:
                p.children.remove(fragment)
                if len(head) > 0:
                    p.children += head
        for e in tail:
            #inherit all children connections in processed fragment
            e.children += fragment.children

    elif fragment.label != '':
        #if source code is missing load the corresponding fragment source first

        fragment.src = util.get_src(fragment.label, model)
        fragment.label = ''
    else:
        raise Exception("Undefined fragment in the elements array")

'''
    TODO: Update me!!!!!!
    Implementation requirement: To reduce the complexity of the initial parser
    the parallel and arbiter statements ",", "|" and "[]" are required to be enclosed 
    within the parenthesis to represent a single block before the internals are parsed. 

    This approach for this version allows simpler manipulation of heads and tails to
    correctly reflect petri-net construct tha relates to confusion and parallel execution
    blk is one of: () or single transition
    Legal : [(blk->blk) [] (blk->blk)]
    Legal : [(blk->blk) [] (blk->blk) [] (blk->blk)]
    Legal : ( blk, blk )
    Legal : ( blk, blk, blk )

    Ilegal : [place->blk [] place->blk]
    Illegal : blk->blk [] blk->blk
    Illegal : [blk->blk [] blk->blk , blk]
    Illegal :  blk, blk 
    Illegal : ( blk, blk [] blk )
    and similar combinations

    Detached sequential block:
    Detached sequential is a special type of block that is not recorded in heads list
    Instead the DETACHED status is returned from segment parsing function that places the detached fragment
    childrens as childrens of its parent.

    Detached occurs when the chain of tokens starts from the explicit place label only.

    Explicit place:
    The explicit place is a definition of a tree place which connections are sepcifically stated in the code

    Explicit place can only occur at the beginning or at the end of the sequential block. Explicit place
    is not placed in the tail and the tail remaing unchanged.

    Confusion block:
    Confusion block works different from others. At the beginning it creates central node to which the sequential 
    paths are connected. If a sequential path contains more than one element this implies gated confusion.
    In such case the created node is connected to second element and the first element is placed
    in the final heads list. 

    When the sequential path contains a single element then this element is connected directly to the created
    place and it is not placed in the final heads list as the syntax indicate non gated confusion

    Gated confusion [ cond -> act [] cond2 -> act2]
    Non-gated confusion [ act [] act]

    Normally all elements present in final head list are connected to previous transition. 
    When an independent condition occurs within confusion block, it should be modeled as detached block
    using explicit place definition

    Example : an action act gated by external input signal i+ [ (P0->i+)->act [] .... The P0 place models
    independent path for i+ 
''' 

class SegmentSequential:
    def __init__(self):
        self.head = None
        self.tail = None

    def out(self, model, heads, tails):
        #output head and tail outside for merging

        if self.head and util.is_explicit_place(model, self.head) == False:
            heads += [self.head]

        if self.tail and util.is_explicit_place(model, self.tail) == False:
            tails += [self.tail]


class SegmentParallel:
    def __init__(self):
        self.head = None
        self.tail = None
        self.final_heads = []
        self.final_tails = []
    
    def transfer(self, sequential_segment):
        #transfer path from sequential segment

        if type(sequential_segment) != SegmentSequential:
            raise Exception('Expected sequential segment')

        self.head = sequential_segment.head

        #tail might be None when place occurs
        if sequential_segment.tail:
            self.tail = sequential_segment.tail

    def next_path(self):
        #start new path

        self.final_heads = self.final_heads + [self.head]
        self.head = None

        #tail might be None when place occurs
        if self.tail:
            self.final_tails = self.final_tails + [self.tail]
        self.tail = None

    def out(self, model, heads, tails):
        #output head and tail outside for merging
        if self.head != None:
            self.next_path()

        #generate place for every input
        #skip if explicit place at the begining or end
        for e in self.final_heads:
            if util.is_explicit_place(model, e) == False:
                place_begin = t.TreePlace()
                place_begin.name = util.gen_place_label(model)
                place_begin.children += [e]
                model.elements += [place_begin]
                heads += [place_begin]

        for e in self.final_tails:
            if util.is_explicit_place(model, e) == False:
                place_end = t.TreePlace()
                place_end.name = util.gen_place_label(model)
                e.children += [place_end]
                model.elements += [place_end]
                tails += [place_end]

        if len(heads) < 2:
            raise Exception('Expected parallel block to have at least two paths')


class SegmentConfusion:
    #multiple output transitions
    #what is the head
    #connect second if more than two in link 
    def __init__(self):
        self.head = None
        self.tail = None
        self.final_heads = []
        self.final_tails = []
    
    def transfer(self, sequential_segment):
        #transfer path from sequential segment

        if type(sequential_segment) != SegmentSequential:
            raise Exception('Expected sequential segment')

        self.head = sequential_segment.head

        #tail might be None when place occurs
        if sequential_segment.tail:
            self.tail = sequential_segment.tail

    def next_path(self):
        #start new path

        self.final_heads = self.final_heads + [self.head]
        self.head = None
        #tail might be None when place occurs
        if self.tail:
            self.final_tails = self.final_tails + [self.tail]
        self.tail = None

    def out(self, model, heads, tails):
        #output head and tail outside for merging
        if self.head != None:
            self.next_path()

        place_begin = t.TreePlace()
        model.elements += [place_begin]
        heads += [place_begin]

        place_begin.name = util.gen_place_label(model)

        #NOTE: Implementation propetrty. If the segment in confusion has chain with multiple children
        #   at the time of processing the block the central place is attached to the children.
        #   This functionality allows for implementation of gated confusion.
        #To achieve regular confusion block use fragment within the selectgion list
        # Might need improvement in next versions
        #place on second child if more than one exist in path

        for i in range(len(self.final_heads)):
            fh = self.final_heads[i]
            e = self.final_tails[i]

            if util.is_explicit_place(model, e) == False:
                tails += [e]
                place_begin.children += [e]

            if util.is_explicit_place(model, fh) == False and fh != e:
                heads += [fh]


        if len(place_begin.children) < 2:
            raise Exception('Expected confusion block to have at least two paths')



def parse_segment(model, head, tail, src):
    #process series of tokens in a segment

    i = 0
    last = len(src)

    #Default segment
    seg = SegmentSequential()

    while(i < last):
        #iterate through every token

        elem = src[i]
        token = syntax.decode_token(elem)
        
        if token == syntax.Token.SQR_BR_R or token == syntax.Token.PAR_R:
            #unexpected closing bracket without opening bracket
            raise Exception('Unexpected closing bracket %s without opening bracket' % elem)
        elif token == syntax.Token.LOOP:
            #loop token detected

            #extract internal sorurce
            block_src = util.extract_block_subarray(i, src)
            tree_fragment = t.TreeFragment()
            tree_fragment.src = block_src[1]
            model.elements += [tree_fragment]

            #create loop fragment
            loop_fragment_end = t.TreeLoopFragmentEnd()
            loop_fragment_begin = t.TreeLoopFragmentBegin()
            loop_fragment_begin.children += [tree_fragment]
            loop_fragment_begin.ref_end = loop_fragment_end
            tree_fragment.children += [loop_fragment_end]
            model.elements += [loop_fragment_begin, loop_fragment_end]

            if seg.head: 
                #something is already in segment
                #uncommon potentially modeling initialization
                #followed by infinite loop
                seg.tail.children += [loop_fragment_begin]
                seg.tail = loop_fragment_end
            else:
                seg.head = loop_fragment_begin
                seg.tail = loop_fragment_end

            i = block_src[0]

        elif token == syntax.Token.SQR_BR_L or token == syntax.Token.PAR_L:
            #opening bracket detected
            #extract source fragment until matching closing bracket
            #and place as source fragment

            block_src = util.extract_block_subarray(i, src)

            tree_fragment = t.TreeFragment()
            tree_fragment.src = block_src[1]
            model.elements += [tree_fragment]

            if seg.head: 
                seg.tail.children += [tree_fragment]
                seg.tail = tree_fragment
            else:
                seg.head = tree_fragment
                seg.tail = tree_fragment

            i = block_src[0]

        elif token == syntax.Token.CONFUSION or token == syntax.Token.CONFUSION_ARB:
            #confusion token encountered

            if type(seg) is not SegmentSequential and type(seg) is not SegmentConfusion:
                raise Exception('Unexpected current segment type %s' % type(seg))

            #transform existing sequential path to confusion block
            #and start new path for further tokens
            if type(seg) is SegmentSequential:
                tmp = SegmentConfusion()
                tmp.transfer(seg)
                seg = tmp
            seg.next_path()

            i = i+1
        elif token == syntax.Token.SEQ or token == syntax.Token.ACT:
            # sequential (;) or (->)
            #add place to the path

            place = t.TreePlace()
            place.name = util.gen_place_label(model)
            model.elements += [place]

            if seg.head:
                seg.tail.children += [place]
                seg.tail = place
            else:
                seg.head = place
                seg.tail = place

            i = i + 1
        elif token == syntax.Token.EPL:
            # (=>) token
            #do nothing

            i = i + 1
        elif token == syntax.Token.PARALLEL:
            #parallel token 

            if type(seg) is not SegmentSequential and type(seg) is not SegmentParallel:
                raise Exception('Unexpected current segment type %s' % type(seg))

            #transform existing sequential path to parallel block (if applicable)
            #and start new path for further tokens
            if type(seg) is SegmentSequential:
                tmp = SegmentParallel()
                tmp.transfer(seg)
                seg = tmp
            seg.next_path()

            i = i+1

        elif token == syntax.Token.SEP:
            #Create a source fragment without any parent child connections
            #Absorb the remainder of tokens for the new fragment
            i = i + 1

            block_src = []

            while(i < last):
                block_src += [src[i]]
                i = i + 1

            tree_fragment = t.TreeFragment()
            tree_fragment.src = block_src
            model.elements += [tree_fragment]

        elif token == syntax.Token.UNKNOWN:
            #other type of token

            #WARNING: this version does not do the sanity check!!!
            if util.is_explicit_place(model, elem):
                #1 test for explicit place token
                    #if place then either detached or no tail
                    #no tail if sequential not empty or parallel
                    #OBSOLETE: assuming correct syntax meaning no a+; P0; b+ but parallel allowed

                #find if there is already an explicit place present 
                place = util.get_place(model, elem)
                if place == None:
                    #if no create one
                    place = t.TreePlace()
                    place.name = elem
                    model.elements += [place]

                #look one before and one after element if there is -> operator
                #if present then attach a place without modifying regular flow

                #NOTE: Limitation, only transition allowed after and before -> operator
                #otherwise thrown an exception
                pre_arrow_present = False
                post_arrow_present = False
                inflow_present = False

                if i > 0:
                    prev = src[i-1]
                    prev_token = syntax.decode_token(prev)
                    if prev_token ==  syntax.Token.EPL:
                        pre_arrow_present = True


                if i < (last-1):
                    nxt = src[i+1]
                    nxt_token = syntax.decode_token(nxt)
                    if nxt_token ==  syntax.Token.EPL:
                        post_arrow_present = True

                if pre_arrow_present == True:
                    #add created place as a child of preceding transition

                    if type(seg.tail) is not t.TreeTransition:
                        raise Exception('Syntax error, preceding element must be a transition')

                    seg.tail.children += [place]

                if post_arrow_present == True:
                    #get element past the arrow, verify that is is a transition and add both
                    # the explicit place and the transition
                    nxt = src[i+2]

                    if util.is_transition(model, nxt) == False:
                        raise Exception('Syntax error, following element must be a transition')

                    #process transition
                    tran = t.TreeTransition()
                    tran.name = nxt
                    model.elements += [tran]

                    if seg.head:
                        seg.tail.children += [tran]
                        seg.tail = tran
                    else:
                        seg.head = tran
                        seg.tail = tran

                    place.children += [tran]
                elif pre_arrow_present == False:
                    inflow_present = True

                    if seg.head:
                        seg.tail.children += [place]
                        seg.tail = place
                    else:
                        seg.head = place
                        seg.tail = place

                if pre_arrow_present == True or inflow_present == True:
                    i = i + 1
                else:
                    #must be post
                    i = i + 3

            elif util.is_transition(model, elem):
                #2 test for transition
                tran = t.TreeTransition()
                tran.name = elem
                model.elements += [tran]

                if seg.head:
                    seg.tail.children += [tran]
                    seg.tail = tran
                else:
                    seg.head = tran
                    seg.tail = tran

                i = i + 1
            elif util.is_fragment(model, elem):
                #3 test for source fragment
                frag = t.TreeFragment()
                frag.label = elem
                model.elements += [frag]

                if seg.head:
                    seg.tail.children += [frag]
                    seg.tail = frag
                else:
                    seg.head = frag
                    seg.tail = frag

                i = i + 1
            else:
                raise Exception('Unknown token %s' % elem)
        else:
            raise Exception('DEBUG POINT 0')

    
    #Obtain final heads and tails
    seg.out(model, head, tail)

    return SegmentParseStatus.DEFAULT

'''

NOTE 1: Exact two loop places migh exist but nonnecting the same loop

apply loop place v2:
    extract all loop places begin and end from main array
    remove loop places from the main array

    for every begin loop place if there are any children places remove them and assign
    their children transitions directly to loop place

    for every end loop place if there are any parent places remove them and assign end loop place
    as child to its parent transitions

    FOR loop_places definitions in header:
        applied = false
        FOR loop_places_begin
            IF exact match in loop_place.satisfied CONTINUE

            get lists of transitions corresponding to the loop place

            IF matching set of transitions present within the set
                create place
                inherit all parents from loop begin
                insert into main array
                assign loop place to satisfied list
                applied = true

        IF applied == false
            EXCEPTION

    remove all loop fragments and references to it f
    remove all places pointing to loop_end
'''

def apply_loop_places(model):
    #extract all loop fragments
    loop_fragment_begin_array = []

    for p in model.elements:
        if type(p) is t.TreeLoopFragmentBegin:
            loop_fragment_begin_array += [p]

    #remove all loop fragments from the main array
    for p in loop_fragment_begin_array:
        model.elements.remove(p)
        model.elements.remove(p.ref_end)

    #For all begin loop places, if there exist child place remove it and assign all its children to loop place
    for p in loop_fragment_begin_array:
        for c in p.children:
            if type(c) is t.TreePlace:
                p.children += c.children
                p.children.remove(c)
                model.elements.remove(c)

    #For all end loop places, if there exist a parent place remove it and assign its parents to the loop place
    for p in loop_fragment_begin_array:
        p_parents = util.get_parents(model, p.ref_end)

        for c in p_parents:
            if type(c) is t.TreePlace:
                for cp in util.get_parents(model, c):
                    cp.children.remove(c)
                    cp.children += [p.ref_end]

                model.elements.remove(c)


    #start processing loop places
    for meta_lp in model.meta.loop_place:
        #throw exception of still false at the end of nested loop
        applied = False

        for lpb in loop_fragment_begin_array:
            #check if possible duplicate was already satisfied
            duplicate = False
            for dupl in lpb.satisfied:
                if util.loop_place_equiv(dupl, meta_lp) == True:
                    duplicate = True

            if duplicate == False:
                #Obtain candidate transitions lists 
                end_array = lpb.children
                begin_array = util.get_parents(model, lpb.ref_end)

                #check if current loop place contains required transitions
                end_match = util.have_all(end_array, meta_lp.output)
                begin_match = util.have_all(begin_array, meta_lp.input)

                
                if begin_match == True and end_match == True:
                    #Create loop place
                    lp = t.TreePlace()
                    lp.name = util.gen_place_label(model)

                    #inherit parents of the loop begin place(if any)
                    for p in util.get_parents(model, lpb):
                        p.children += [lp]

                    #assign postset
                    for e in end_array:
                        if e.name in meta_lp.output:
                            lp.children += [e]

                    #assign preset
                    for b in begin_array:
                        if b.name in meta_lp.input:
                            b.children += [lp]


                    #insert into main array
                    model.elements += [lp]
                    
                    #assign loop place to satisfied list
                    lpb.satisfied += [meta_lp]
                    applied = True
                    break

        #exception of not applied!!!
        if applied == False:
            raise Exception('Missing place for [%s]->[%s]' % (meta_lp.input, meta_lp.output))

    #remove any references to loop places
    for e in model.elements:
        for lpb in loop_fragment_begin_array:
            if lpb in e.children:
                e.children.remove(lpb)

            if lpb.ref_end in e.children:
                e.children.remove(lpb.ref_end)


def remove_redundant_places(model):

    #WARNING!!!!!! Order of the operations matter!!!!!!
    #NOTE: This is an unoptimized version of the function
    #the implementation goal is to expose list of possible 
    #redundant configurations

    #places with one input place and multiple output places STRICTLY
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #skip marked place
                if elem.marking:
                    continue

                cnd1 = False
                cnd2 = False

                parents = util.get_parents(model, elem)

                if len(parents) == 1:
                    if type(parents[0]) is t.TreeTransition:
                        cnd1 = True

                if len(elem.children) > 1:
                    cnd2 = True
                    for c in elem.children:
                        if type(c) is not t.TreePlace:
                            cnd2 = False

                if cnd1 and cnd2:
                    parents[0].children.remove(elem)
                    parents[0].children += elem.children
                    model.elements.remove(elem)
                    done = False


    #places with one input and one output transition STRICTLY
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #skip marked place
                if elem.marking:
                    continue

                cnd1 = False
                cnd2 = False

                parents = util.get_parents(model, elem)

                if len(parents) == 1:
                    if type(parents[0]) is t.TreeTransition:
                        cnd1 = True

                if len(elem.children) == 1:
                    if type(elem.children[0]) == t.TreeTransition:
                        cnd2 = True

                if cnd1 and cnd2:
                    parents[0].children.remove(elem)
                    parents[0].children += [elem.children[0]]
                    model.elements.remove(elem)
                    done = False

    #places with one input place and one output place or transition STRICTLY
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #skip marked place
                if elem.marking:
                    continue

                cnd1 = False
                cnd2 = False

                parents = util.get_parents(model, elem)

                if len(parents) == 1:
                    if type(parents[0]) is t.TreePlace:
                        cnd1 = True

                if len(elem.children) == 1:
                    if type(elem.children[0]) is t.TreePlace or type(elem.children[0]) is t.TreeTransition:
                        cnd2 = True

                if cnd1 and cnd2:
                    parents[0].children.remove(elem)
                    parents[0].children += [elem.children[0]]
                    model.elements.remove(elem)
                    done = False



    #places with one input transition and one output place STRICTLY
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #skip marked place
                if elem.marking:
                    continue

                cnd1 = False
                cnd2 = False

                parents = util.get_parents(model, elem)

                if len(parents) == 1:
                    if type(parents[0]) is t.TreeTransition:
                        cnd1 = True

                if len(elem.children) == 1:
                    if type(elem.children[0]) == t.TreePlace:
                        cnd2 = True

                if cnd1 and cnd2:
                    parents[0].children.remove(elem)
                    parents[0].children += [elem.children[0]]
                    model.elements.remove(elem)
                    done = False


    #places
    #one or more parents
    #have exactly one child that is place and the child have more than one parents
    #this corrects the double place which is a byproduct of nested confusion blocks
    #where internal confusion block does not have any following sequential transitions
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #if the element is a place
                if elem.marking:
                    #skip marked place
                    continue

                # get array of element parents
                parents = util.get_parents(model, elem)

                if len(elem.children) == 1 and len(parents) > 0:
                    child = elem.children[0]
                    if (type(child) is t.TreePlace) and (len(util.get_parents(model, child)) > 1):
                        #remove element in questions and
                        # assign its child to all parents
                        model.elements.remove(elem)


                        for p in parents:
                            p.children.remove(elem)
                            p.children += [child]

                        done = False


    #places with one or more input transitions and one or more input places
    #and single output transition STRICTLY
    #this corrects the incorrect connection for gated confusion coming
    #out from parser
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #if the element is a place
                if elem.marking:
                    #skip marked place
                    continue

                # get array of element parents
                parents = util.get_parents(model, elem)
                parent_tran_cnt = 0
                parent_place_cnt = 0

                for p in parents:
                    if type(p) is t.TreeTransition:
                        parent_tran_cnt += 1

                    if type(p) is t.TreePlace:
                        parent_place_cnt += 1

                if (len(elem.children) == 1) and (parent_tran_cnt > 0) and (parent_place_cnt > 0):
                    if type(elem.children[0]) is t.TreeTransition:
                        #remove element in questions and
                        # assign its child to all parents
                        model.elements.remove(elem)

                        child = elem.children[0]

                        for p in parents:
                            p.children.remove(elem)
                            p.children += [child]

                        done = False


    #do not remove places with 0 or more than one outputs
    # the 0 outputs means loop ending place

    #places
    #one or more parents
    #have exactly one child that is place and the child have exactly one parent
    #also the child has multiple children
    #this correct the redundant case where we have an explicit place right before confision block
    #the confusion block starting place ingerits parents of explicit place
    done = False
    while not done:
        done = True
        for elem in model.elements:
            if type(elem) is t.TreePlace:
                #if the element is a place
                if elem.marking:
                    #skip marked place
                    continue

                # get array of element parents
                parents = util.get_parents(model, elem)

                if len(elem.children) == 1 and len(parents) > 1:
                    child = elem.children[0]
                    if (type(child) is t.TreePlace) and (len(child.children) > 1):
                        #remove element in questions and
                        # assign its child to all parents
                        model.elements.remove(elem)


                        for p in parents:
                            p.children.remove(elem)
                            p.children += [child]

                        done = False


def apply_markings(model):

    for m in model.meta.markings:
        place = util.match_strictly(model, m.input, m.output, t.TreePlace)

        if len(place) == 0:
            #attempt to find one to one transition
            #many to many without place are invalid
            if (len(m.input) == 1) and (len(m.output) == 1):
                place = util.find_transition_one_to_one(model, m.input[0], m.output[0])
                if len(place) == 1:
                    p = t.TreePlace()
                    p.name = util.gen_place_label(model)
                    p.marking = True
                    model.elements += [p]

                    s = place[0][0]
                    d = place[0][1]

                    s.children.remove(d)
                    s.children += [p]
                    p.children += [d]

                elif len(place) == 0:
                    raise Exception('Could not locate marking [%s]->[%s]' % (m.input, m.output))
                elif len(place) > 1:
                    raise Exception('Multiple candidates marking inconclusive [%s]->[%s]' % (m.input, m.output))

            else:
                raise Exception('Invalid marking without place [%s]->[%s]' % (m.input, m.output))
        elif len(place) > 1:
            raise Exception('Multiple candidates marking inconclusive [%s]->[%s]' % (m.input, m.output))
        else:
            place[0].marking = True



