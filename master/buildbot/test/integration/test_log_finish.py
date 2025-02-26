# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members


from twisted.internet import defer

from buildbot.plugins import steps
from buildbot.process.results import EXCEPTION
from buildbot.process.results import SUCCESS
from buildbot.test.util.integration import RunMasterBase


class TestLog(RunMasterBase):
    # master configuration

    @defer.inlineCallbacks
    def setup_config(self, step):
        c = {}
        from buildbot.config import BuilderConfig
        from buildbot.process.factory import BuildFactory
        from buildbot.plugins import schedulers

        c['schedulers'] = [
            schedulers.AnyBranchScheduler(
                name="sched",
                builderNames=["testy"])]

        f = BuildFactory()
        f.addStep(step)
        c['builders'] = [
            BuilderConfig(name="testy",
                          workernames=["local1"],
                          factory=f)]
        yield self.setup_master(c)

    @defer.inlineCallbacks
    def test_shellcommand(self):
        testcase = self

        class MyStep(steps.ShellCommand):

            def _newLog(self, name, type, logid, logEncoding):
                r = super()._newLog(name, type, logid, logEncoding)
                testcase.curr_log = r
                return r

        step = MyStep(command='echo hello')

        yield self.setup_config(step)

        change = dict(branch="master",
                      files=["foo.c"],
                      author="me@foo.com",
                      committer="me@foo.com",
                      comments="good stuff",
                      revision="HEAD",
                      project="none")
        build = yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)
        self.assertEqual(build['buildid'], 1)
        self.assertEqual(build['results'], SUCCESS)
        self.assertTrue(self.curr_log.finished)

    @defer.inlineCallbacks
    def test_mastershellcommand(self):
        testcase = self

        class MyStep(steps.MasterShellCommand):

            def _newLog(self, name, type, logid, logEncoding):
                r = super()._newLog(name, type, logid, logEncoding)
                testcase.curr_log = r
                return r

        step = MyStep(command='echo hello')

        yield self.setup_config(step)

        change = dict(branch="master",
                      files=["foo.c"],
                      author="me@foo.com",
                      committer="me@foo.com",
                      comments="good stuff",
                      revision="HEAD",
                      project="none")
        build = yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)
        self.assertEqual(build['buildid'], 1)
        self.assertEqual(build['results'], SUCCESS)
        self.assertTrue(self.curr_log.finished)

    @defer.inlineCallbacks
    def test_mastershellcommand_issue(self):
        testcase = self

        class MyStep(steps.MasterShellCommand):

            def _newLog(self, name, type, logid, logEncoding):
                r = super()._newLog(name, type, logid, logEncoding)
                testcase.curr_log = r
                testcase.patch(r, "finish", lambda: defer.fail(RuntimeError('Could not finish')))
                return r

        step = MyStep(command='echo hello')

        yield self.setup_config(step)

        change = dict(branch="master",
                      files=["foo.c"],
                      author="me@foo.com",
                      committer="me@foo.com",
                      comments="good stuff",
                      revision="HEAD",
                      project="none")
        build = yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)
        self.assertEqual(build['buildid'], 1)
        self.assertFalse(self.curr_log.finished)
        self.assertEqual(build['results'], EXCEPTION)
        errors = self.flushLoggedErrors()
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.getErrorMessage(), 'Could not finish')
