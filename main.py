# CSP to STG parser v 0.0.1concept_preview_alpha
#
# Tomasz Chadzynski 
# San Jose State University, 2020
# 
# This software is provided AS IS and comes witn no warranty
#

import sys
import p_types as t
import preprocessor as pp
import parser as pa
import petrify_converter as pc


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Invalid argument")
    
    print("Loading sources: %s" % sys.argv[1])
    model = pp.load(sys.argv[1])
    print('\n################## Begin preprocess #####################\n')
    pp.process(model)
    print('\n################## Begin parsing ########################\n')
    pa.gen_tree(model)
    print('\n################## Writing output for petrify############\n')
    src = pc.to_petrify(model)
    print(src)
    pc.save_file(model, src) 

