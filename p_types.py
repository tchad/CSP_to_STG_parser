# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes with no warranty
#

#Classes modeling the PetriNet graph
from enum import Enum

class TreeElement():
    def __init__(self):
        self.children = []

class TreePlace(TreeElement):
    def __init__(self):
        super().__init__()
        self.marking = False
        self.name = ''

class TreeTransition(TreeElement):
    def __init__(self):
        super().__init__()
        self.name = ''

class TreeFragment(TreeElement):
    '''
    Fragment has either the src field populated while 
    the interpreter caught opening parenthesis, or 
    label refering to a fragment in other part of the 
    source code
    '''
    def __init__(self):
        super().__init__()
        self.src = []
        self.label = ''
        self.name = '_TreeFragment'
        self.separate = False

class TreeLoopFragmentBegin(TreeElement):
    '''
    Encapsulates loop operator until the final resolution
    of loop places.
    '''
    def __init__(self):
        super().__init__()
        self.name = '_TreeLoopFragmentBegin'
        self.ref_end = None
        self.satisfied = []

class TreeLoopFragmentEnd(TreeElement):
    '''
    Encapsulates loop operator until the final resolution
    of loop places.
    '''
    def __init__(self):
        super().__init__()
        self.name = '_TreeLoopFragmentEnd'


#Classes modeling model meta description

class MetaModelType(Enum):
    CONTROLLER = 1
    BEHAV = 2
    UNDEFINED = 0
    
class MetaPlace():
    def __init__(self):
        self.input = []
        self.output = []

class Meta():
    def __init__(self):
        self.model_type = MetaModelType.UNDEFINED
        self.inputs = []
        self.outputs = []
        self.main = ''
        self.fragments = []
        self.loop_place = []
        self.explicit_place = []
        self.markings = []

    def validate(self):
        pass

class CodeFragment():
    def __init__(self, l, s):
        self.label = l
        self.src = s

class Model():
    def __init__(self):
        self.raw_src = ''
        self.interface_raw_src = ''
        self.code_raw_src = ''

        self.meta = None
        self.code_fragments = []

        self.elements = []


