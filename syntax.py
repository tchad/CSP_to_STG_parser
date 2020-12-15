# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes with no warranty
#

# Supporting syntax tokens

import regex
from enum import Enum

class Token(Enum):
    UNKNOWN = 0
    SQR_BR_L = 1
    SQR_BR_R = 2
    CONFUSION = 3
    PAR_L = 4
    PAR_R = 5
    CONFUSION_ARB = 6
    ACT = 7
    SEQ = 8
    PARALLEL = 9
    LOOP = 10
    EPL = 11
    SEP = 12

LOOKUP_TAB = [
        (regex.STR_SQR_BR_L, Token.SQR_BR_L),
        (regex.STR_SQR_BR_R, Token.SQR_BR_R),
        (regex.STR_CONFUSION, Token.CONFUSION),
        (regex.STR_PAR_L, Token.PAR_L),
        (regex.STR_PAR_R, Token.PAR_R),
        (regex.STR_CONFUSION_ARB, Token.CONFUSION_ARB),
        (regex.STR_ACT, Token.ACT),
        (regex.STR_SEQ, Token.SEQ),
        (regex.STR_PARALLEL, Token.PARALLEL),
        (regex.STR_LOOP, Token.LOOP),
        (regex.STR_EPL, Token.EPL),
        (regex.STR_SEP, Token.SEP)
        ]

def decode_token(label):
    for elem in LOOKUP_TAB:
        if label == elem[0]:
            return elem[1]

    return Token.UNKNOWN


