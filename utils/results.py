import os, os.path as op
import subprocess as sp

def Zip_Results(context):
    os.chdir(context.output_dir)
    # If the output/result.anat path exists, zip regardless of exit status
    # Clean input_file_basename to lack esc chars and extension info
    input_file_basename = context.custom_dict['input_file_basename']
    result_dir = context.custom_dict['result_dir']+'.maths'
    if op.exists(op.join(context.work_dir, result_dir)):
        context.log.info(
            'Zipping '+op.join(context.work_dir, result_dir) + ' directory.'
        )
        # For results with a large number of files, provide a manifest.
        # Capture the stdout/stderr in a file handle or for logging.
            
        command0 = ['tree', '-shD', '-D', op.join(context.work_dir,result_dir)]
        with open(input_file_basename + '_output_manifest.txt', 'w') as f:
            sp.run(command0, stdout = f)
        command1 = ['zip', '-r', result_dir + '.zip', \
                    op.join(context.work_dir, result_dir)]
        context.log.info(command1)
        sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        context.log.info(
            'No results directory, \
            /flywheel/v0/work/' + \
            result_dir + ', to zip.')