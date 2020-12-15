# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes witn no warranty
#

# Supporting regular expressions

import re

HEADER_CODE_BREAK = r"^(.*)endinterface(.*)"

HEADER_MODULE_CONTROLLER = r"module\scontroller;"
HEADER_MODULE_BEHAV = r"module\sbehav;"
HEADER_MAIN = r"main\s([A-Za-z0-9_]*);"
HEADER_FRAGMENT = r"fragment\s([A-Za-z0-9_!?]*);"
HEADER_INPUTS = r"inputs\s([A-Za-z0-9_\s]*);"
HEADER_OUTPUTS = r"outputs\s([A-Za-z0-9_\s]*);"
HEADER_LOOP_PLACE = r"loop_place\s\[([A-Za-z0-9_\s+-]*)\]->\[([A-Za-z0-9_\s+-]*)\];"
HEADER_EXPLICIT_PLACE = r"explicit_place\s(P[0-9\s]*);"
HEADER_MARKING = r"marking\s\[([A-Za-z0-9_\s+-]*)\]->\[([A-Za-z0-9_\s+-]*)\];"

module_controller = re.compile(HEADER_MODULE_CONTROLLER)
module_behav = re.compile(HEADER_MODULE_BEHAV)
main = re.compile(HEADER_MAIN)
fragment = re.compile(HEADER_FRAGMENT)
inputs = re.compile(HEADER_INPUTS)
outputs = re.compile(HEADER_OUTPUTS)
loop_place = re.compile(HEADER_LOOP_PLACE)
explicit_place = re.compile(HEADER_EXPLICIT_PLACE)
marking = re.compile(HEADER_MARKING)

def label_fix(s):
    #quick fix for the ? sign in labels
    s_str = r''
    for c in s:
        if c == '?':
            s_str += r'\?'
        else:
            s_str += c

    return s_str

#syntax parsing helpers
#Syntax elements: [ ] [] ( ) | -> ; , *[ => :

TEMPL_SQR_BR_L = r"([^\*])\[([^\]])"
SYNTAX_SQR_BR_L = r"\1 [ \2"
STR_SQR_BR_L = r"["

TEMPL_SQR_BR_R = r"([^\[])\]"
SYNTAX_SQR_BR_R = r"\1 ] "
STR_SQR_BR_R = r"]"

TEMPL_CONFUSION = r"\[\]"
SYNTAX_CONFUSION = r" [] "
STR_CONFUSION = r"[]"

TEMPL_PAR_L = r"\("
SYNTAX_PAR_L = r" ( "
STR_PAR_L = r"("

TEMPL_PAR_R = r"\)"
SYNTAX_PAR_R = r" ) "
STR_PAR_R = r")"

TEMPL_CONFUSION_ARB = r"\|"
SYNTAX_CONFUSION_ARB = r" | "
STR_CONFUSION_ARB = r"|"

TEMPL_ACT = r"->"
SYNTAX_ACT = r" -> "
STR_ACT = r"->"

TEMPL_SEQ = r";"
SYNTAX_SEQ = r" ; "
STR_SEQ = r";"

TEMPL_PARALLEL = r","
SYNTAX_PARALLEL = r" , "
STR_PARALLEL = r","

TEMPL_LOOP = r"\*\["
SYNTAX_LOOP = r" *[ "
STR_LOOP = r"*["

TEMPL_EPL = r"=>"
SYNTAX_EPL = r" => "
STR_EPL = r"=>"

TEMPL_SEP = r":"
SYNTAX_SEP = r" : "
STR_SEP = r":"

