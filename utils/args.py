import shutil
import re
import os, os.path as op
import subprocess as sp

def build(context):
    """
    Build a dictionary of key:value command-line parameter names:values
    These will be validated and assembled into a command-line below.
    """
    config = context.config
    params = {}
    # Due to escape characters, we need to move the input files to
    # non-escaped character versions of themselves. the fsl-anat
    # command does parse spaces (escaped or otherwise)
    nonSpaced_path=re.sub(
        '[^0-9a-zA-Z./]+', '_', context.get_input_path('Image')
    )
    # A "move" will not work... must be "copy"
    if nonSpaced_path != context.get_input_path('Image'):
        shutil.copy(context.get_input_path('Image'),
                    nonSpaced_path)

    params['i'] = nonSpaced_path
    # fsl_anat will create the work directory and name it
    # /flywheel/v0/work/<input_file basename>_result.anat
    # Automatically appending the ".anat"
    # NOTE: Always escape for special bash characters
    input_file_basename =   re.sub('[^0-9a-zA-Z./]+', '_',
                            context.get_input("Image")['location']['name']
                        )
    if input_file_basename.endswith('.nii.gz'):
        input_file_basename = input_file_basename.replace('.nii.gz', '')
    if input_file_basename.endswith('.nii'):
        input_file_basename = input_file_basename.replace('.nii', '')
    context.custom_dict['input_file_basename'] = input_file_basename
    result_dir = input_file_basename + '_result'
    context.custom_dict['result_dir']=result_dir
    params['o'] = op.join(context.work_dir, result_dir)
    for key in config.keys():
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                params[key] = True
        else:
            # if the key-value is zero, we skip and use the defaults
            if config[key] != 0:
                params[key] = config[key]
    context.custom_dict['params'] = params


def validate(context):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations.
    """
    log = context.log
    params = context.custom_dict['params']
    keys = params.keys()
    # Test for input existence
    # os.path.exists does not like escape characters
    
    if not op.exists(params['i']):
        raise Exception('Input File Not Found: ' + params['i'])



def BuilCommandList(command, ParamList):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to
    be put into the command list as such ("-k value" or "--key=value")
    """
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

def execute(context,dry_run=False):
    command = context.custom_dict['command']
    command = BuilCommandList(command, context.custom_dict['params'])
    context.log.info('FSLMATHS Command:'+' '.join(command))
    if not dry_run:
        environ = context.custom_dict['environ']
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