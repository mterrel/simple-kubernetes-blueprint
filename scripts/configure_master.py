#!/usr/bin/env python

import pwd
import grp
import os
import getpass
import subprocess
import tempfile
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

def sudo_write_file(dest_file, contents):
    ctx.logger.info('creating file %s' % dest_file)

    f = None
    temp_name = None
    try:
        try:
            fd,temp_name = tempfile.mkstemp()
            f = os.fdopen(fd, 'w')
            f.write(contents)
        finally:
            if f: f.close()
            elif temp_name: os.close(fd)
        execute_command('sudo cp %s %s' % (temp_name, dest_file))
    finally:
        if temp_name:
            os.remove(temp_name)


if __name__ == '__main__':

    # Create config file
    kubeadm_config = '''
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
apiServerExtraArgs:
  basic-auth-file: /etc/kubernetes/basic.auth
'''
    basic_auth = '''
admin,admin,100
'''

    sudo_write_file('/etc/kubernetes/kubeadm.config', kubeadm_config)
    sudo_write_file('/etc/kubernetes/basic.auth', basic_auth)

    # Start the Kube Master
    start_output = execute_command('sudo kubeadm init --skip-preflight-checks --config /etc/kubernetes/kubeadm.config')
    for line in start_output.split('\n'):
        if 'kubeadm join' in line:
            ctx.instance.runtime_properties['join_command'] = line.lstrip()

    # Add the kubeadmin config to environment
    agent_user = getpass.getuser()
    uid = pwd.getpwnam(agent_user).pw_uid
    gid = grp.getgrnam('docker').gr_gid
    admin_file_dest = os.path.join(os.path.expanduser('~'), 'admin.conf')

    execute_command('sudo cp {0} {1}'.format('/etc/kubernetes/admin.conf', admin_file_dest))
    execute_command('sudo chown {0}:{1} {2}'.format(uid, gid, admin_file_dest))

    with open(os.path.join(os.path.expanduser('~'), '.bashrc'), 'a') as outfile:
        outfile.write('export KUBECONFIG=$HOME/admin.conf')
    os.environ['KUBECONFIG'] = admin_file_dest
    execute_command('kubectl apply -f https://git.io/weave-kube-1.6')

