#!/usr/bin/env python3

import codecs
import json
import logging
import copy
import os
import os.path as op
import sys
import subprocess as sp
import shutil
import flywheel


def Build_FSL_Anat_Params(context):
    """
    Build a dictionary of key:value command-line parameter names:values
    These will be validated and assembled into a command-line below.
    """
    config = context.config
    Params = {}
    Params['i'] = context.get_input_path('Image')
    # fsl_anat will create the output directory and name it
    # /flywheel/v0/output/<input_file basename>_result.anat
    # Automatically appending the ".anat"
    # NOTE: The constructed command executed by sp.run ignores spaces
    #       However, if run with "shell=True" we need to escape those 
    #       spaces.
    input_file_basename = context.get_input("Image")['location']['name']
    Params['o'] = op.join(context.output_dir, input_file_basename + '_result')
    for key in config.keys():
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                Params[key] = True
        else:
            if len(key) == 1:
                Params[key] = config[key]
            else:
                # if the key-value is zero, we skip and use the defaults
                if config[key] != 0:
                    Params[key] = config[key]
    return Params


def Validate_FSL_Anat_Params(Params, log):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations.
    """
    keys = Params.keys()
    # Test for input existence
    if not op.exists(Params['i']):
        raise Exception('Input File Not Found')

    if ('betfparam' in keys) and ('nononlinreg' in keys):
        if(Params['betfparam'] > 0.0):
            raise Exception(
                'For betfparam values > zero, \
                nonlinear registration is required.')

    if ('s' in keys):
        if Params['s'] == 0:
            log.warning(
                'The value of ' + str(Params['s']) +
                ' for -s may cause a singular matrix')


def BuilCommandList(command, ParamList):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to
    be put into the command list as such ("-k value" or "--key=value")
    """
    print(ParamList)
    for key in ParamList.keys():
        # Single character command-line parameters preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(ParamList[key])) != 0:
                command.append(str(ParamList[key]))
        # Multi-Character command-line parameters preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(ParamList[key]) == bool:
                if ParamList[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, without value include without value
                # (e.g. '--key'), else include value (e.g. '--key=value')
                if len(str(ParamList[key])) == 0:
                    command.append('--' + key)
                else:
                    command.append('--' + key + '=' + str(ParamList[key]))
    return command


if __name__ == '__main__':
    context = flywheel.GearContext()
    config = context.config
    # Initialize Custom Logging
    # Timestamps with logging assist debugging algorithms
    # With long execution times
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
                fmt='%(levelname)s - %(name)-8s - %(asctime)s -  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger = logging.getLogger('flywheel/fsl-anat:0.1.7_5.0.9')
    logger.addHandler(handler)
    context.log = logger
    context.log.setLevel(logging.INFO)

    # context.init_logging()
    context.log_config()

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    # Execute in try except block
    try:
        # Build a parameter dictionary specific for fsl_anat
        fsl_params = Build_FSL_Anat_Params(context)
        # Validate the fsl_anat parameter dictionary
        # Raises Exception on fail
        Validate_FSL_Anat_Params(fsl_params, context.log)
        # Build command-line string for subprocess to execute
        command = ['fsl_anat']
        command = BuilCommandList(command, fsl_params)
        context.log.info('FSL_Anat Command:'+' '.join(command))

        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)

        context.log.info(result.returncode)
        context.log.info(result.stdout)

        if result.returncode != 0:
            context.log.error('The command:\n ' +
                              ' '.join(command) +
                              '\nfailed. See log for debugging.')
            context.log.error(result.stderr)
            os.sys.exit(result.returncode)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.log.error(e)
        context.log.error('Cannot execute FLS Anat commands.')
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory
        # This executes regardless of errors or exit status,
        # 'exit'!=0 is treated like an exception
        # Unless otherwise specified, zip entire results and delete directory
        os.chdir(context.output_dir)
        # If the output/result.anat path exists, zip regardless of exit status
        input_file_basename = context.get_input("Image")['location']['name']
        result_dir = input_file_basename + '_result.anat'
        if op.exists('/flywheel/v0/output/' + result_dir):
            context.log.info(
                'Zipping /flywheel/v0/output/' + result_dir + ' directory.')
            # For results with a large number of files, provide a listing.
            # The subprocess.run routine needs 'shell=True' to redirect to a
            # file or use wildcards. Otherwise, we capture the stdout/stderr.
            # Also, file names with spaces must be 'escaped' in order to work.
            result0 = sp.run(
                'tree -sh --du -D ' + \
                result_dir.replace(' ','\\ ') + \
                ' > ' + \
                input_file_basename.replace(' ','\\ ') + \
                '_output_manifest.txt', shell=True)
            print(result0.returncode, result0.stderr, result0.stdout)
            command1 = ['zip', '-r', result_dir + '.zip', result_dir]
            result1 = sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
            command2 = ['rm', '-rf', '/flywheel/v0/output/' + result_dir]
            result2 = sp.run(command2, stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            context.log.info(
                'No results directory, \
                /flywheel/v0/output/' + \
                result_dir + ', to zip.')
