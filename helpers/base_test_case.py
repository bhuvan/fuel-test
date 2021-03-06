#!/usr/bin/env python

import unittest
from abc import abstractproperty
from ci.ci_base import CiBase
from settings import ERROR_PREFIX, WARNING_PREFIX
from helpers.functions import upload_recipes, upload_keys, write_config


class BaseTestCase(unittest.TestCase):
    """
    BaseTestCase bases on unittest -- python library.
    """
    @abstractproperty
    def ci(self):
        """
        :rtype : CiBase
        """
        pass

    def environment(self):
        """
        Return environment.
        """
        return self.ci().environment()

    def nodes(self):
        """
        Return list of nodes.
        """
        return self.ci().nodes()

    def remote(self):
        """
        Return remote access to master node by login/password.
        """
        return self.environment().node_by_name('master').remote('public', login='root', password='r00tme')

    def update_modules(self):
        """
        Update puppet modules and ssh keys on master node.
        """
        upload_recipes(self.remote())
        upload_keys(self.remote())


    def assertResult(self, result):
        """
        Checking the result on error.
        """
        stderr = filter(lambda x: x.find('PYCURL ERROR 22') == -1, result['stderr'])
        stderr = filter(lambda x: x.find('Trying other mirror.') == -1, stderr)
        self.assertEqual([], stderr, stderr)
        errors, warnings = self.parse_out(result['stdout'])
        self.assertEqual([], errors, errors)
        self.assertEqual([], warnings, warnings)

    def parse_out(self, out):
        """
        Find errors in output.
        """
        errors = []
        warnings = []
        for line in out:
            if (line.find(ERROR_PREFIX) < 15) and (line.find(ERROR_PREFIX) != -1):
                if line.find("Loading failed for one or more files") == -1:
                    if line.find('to_stderr:') == -1:
                        errors.append(line)
            if (line.find(WARNING_PREFIX) < 15) and (line.find(WARNING_PREFIX) != -1):
                if line.find(
                    '# Warning: Disabling this option means that a compromised guest can') == -1:
                    if line.find("Loading failed for one or more files") == -1:
                        warnings.append(line)
        return errors, warnings

    def do(self, nodes, command):
        """
        Execute command on nodes.
        """
        results = []
        for node in nodes:
            print "node", node.get_ip_address_by_network_name("internal")
            remote = node.remote('internal', login='root', password='r00tme')
            results.append(remote.sudo.ssh.execute(command, verbose=True))
        return results

    def validate(self, nodes, command):
        """
        Validate result with expected.
        """
        results = self.do(nodes, command)
        for result in results:
            self.assertResult(result)