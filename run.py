#!/usr/bin/env python3

import codecs
import json
import copy
import os
import os.path as op
import sys
import flywheel

from utils import args, results, log

if __name__ == '__main__':
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    #get_custom_logger is defined in utils.py
    context.log = log.get_custom_logger('[flywheel:fslmaths]')

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    # This gear will use a "custom_dict" dictionary as a custom-user field 
    # on the gear context.
    context.custom_dict ={}

    context.custom_dict['environ'] = environ

    # Execute in try except block
    try:
        # Build a parameter dictionary specific for fsl_anat
        args.build(context)
        # Validate the fsl_anat parameter dictionary
        # Raises Exception on fail
        args.validate(context)
        # Build command-line string for subprocess to execute
        context.custom_dict['command'] = ['fslmaths']

        args.execute(context)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.log.error(e)
        context.log.error('Cannot execute FSLMATHS commands.')
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory
        # This executes regardless of errors or exit status,
        # 'exit'!=0 is treated like an exception
        # Unless otherwise specified, zip entire results and delete directory
        results.Zip_Results(context)
