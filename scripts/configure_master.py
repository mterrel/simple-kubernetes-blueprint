#!/usr/bin/env python

import pwd
import grp
import os
import getpass
import py.path
from cloudify import ctx

from ubs import plugins
plugins.load('ubs.utils')
from ubs.utils import run_cmd

etc_admin_conf = '/etc/kubernetes/admin.conf'
user_conf = os.path.expanduser('~/admin.conf')


def start_cluster():
    # Using existence of user admin.conf as check on whether kubeadm has run
    # successfully once. Note that doesn't mean k8s is fully up and running; it
    # just means we shouldn't run kubeadm again.
    conf_path = py.path.local(user_conf)
    if conf_path.check():
        ctx.logger.debug("Kubeadm already started. Skipping.")
        return

    # Start the Kube Master
    start_output = run_cmd(['kubeadm', 'init', '--skip-preflight-checks'],
                           sudo=True)
    for line in start_output.split('\n'):
        if 'kubeadm join' in line:
            ctx.instance.runtime_properties['join_command'] = line.lstrip()

    # Add the kubeadmin config to environment
    agent_user = getpass.getuser()
    uid = pwd.getpwnam(agent_user).pw_uid
    gid = grp.getgrnam('docker').gr_gid

    run_cmd(['cp', etc_admin_conf, user_conf], sudo=True)
    run_cmd(['chown', '%s:%s' % (uid, gid), user_conf], sudo=True)


    # TODO: this is bash-specific. Either mandate that the agent user uses
    #       bash or deal appropriately with all shells (ugh) or ensure
    #       config is always set on kubectl a different way
    with open(os.path.expanduser('~/.bashrc'), 'a') as outfile:
        outfile.write('export KUBECONFIG=$HOME/admin.conf')

def start_networking():
    # TODO: This should be able to start any networking, not just weave
    os.environ['KUBECONFIG'] = user_conf
    if 'weave-net' in run_cmd('kubectl get daemonset --all-namespaces'):
        # Weave already started
        return
    run_cmd(('kubectl apply -n kube-system '
             '-f "https://cloud.weave.works/k8s/net?k8s-version='
             '$(kubectl version | base64 | tr -d \'\n\')"'),
             shell=True)


def main():
    start_cluster()
    start_networking()


if __name__ == '__main__':
    main()
