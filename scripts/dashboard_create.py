#!/usr/bin/env python

import pwd
import grp
import os
import getpass
import subprocess
from cloudify import ctx

class CmdException(Exception):
    pass

def execute_command(_command):

    ctx.logger.debug('_command {0}.'.format(_command))

    subprocess_args = {
        'args': _command.split(),
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    ctx.logger.debug('subprocess_args {0}.'.format(subprocess_args))

    process = subprocess.Popen(**subprocess_args)
    output, error = process.communicate()

    ctx.logger.debug('command: {0} '.format(_command))
    ctx.logger.debug('output: {0} '.format(output))
    ctx.logger.debug('error: {0} '.format(error))
    ctx.logger.debug('process.returncode: {0} '.format(process.returncode))

    if process.returncode:
        err = 'Running `{0}` returns error.'.format(_command)
        ctx.logger.error(err)
        raise CmdException(err)

    return output


if __name__ == '__main__':

    ctx.logger.debug('starting kubernetes dashboard')

    execute_command('kubectl create -f https://git.io/kube-dashboard')
