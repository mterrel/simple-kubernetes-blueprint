#!/usr/bin/env python

import os
import os.path
import subprocess
from cloudify import ctx

import ubs.plugins
from ubs.utils import run_cmd


if __name__ == '__main__':
    try:
        ctx.logger.info('Starting Kubernetes dashboard')
        # TODO: Should pull this from some node runtime property
        os.environ['KUBECONFIG'] = os.path.expanduser('~/admin.conf')
        run_cmd('kubectl create -f https://git.io/kube-dashboard')
    except:
        _, ex, traceback = sys.exc_info()
        raise NonRecoverableError('Dashboard: Error installing',
                                  causes=[exception_to_error_cause(ex,
                                                                   traceback)])

