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
# Copyright Manba Team

from twisted.internet import defer
from twisted.trial import unittest

from buildbot.test.fake.web import FakeRequest
from buildbot.test.fake.web import fakeMasterForHooks
from buildbot.test.reactor import TestReactorMixin
from buildbot.www import change_hook
from buildbot.www.hooks.bitbucket import _HEADER_EVENT

gitJsonPayload = b"""{
    "canon_url": "https://bitbucket.org",
    "commits": [
        {
            "author": "marcus",
            "branch": "master",
            "files": [
                {
                    "file": "somefile.py",
                    "type": "modified"
                }
            ],
            "message": "Added some more things to somefile.py",
            "node": "620ade18607a",
            "parents": [
                "702c70160afc"
            ],
            "raw_author": "Marcus Bertrand <marcus@somedomain.com>",
            "raw_node": "620ade18607ac42d872b568bb92acaa9a28620e9",
            "revision": null,
            "size": -1,
            "timestamp": "2012-05-30 05:58:56",
            "utctimestamp": "2012-05-30 03:58:56+00:00"
        }
    ],
    "repository": {
        "absolute_url": "/marcus/project-x/",
        "fork": false,
        "is_private": true,
        "name": "Project X",
        "owner": "marcus",
        "scm": "git",
        "slug": "project-x",
        "website": "https://atlassian.com/"
    },
    "user": "marcus"
}"""

mercurialJsonPayload = b"""{
    "canon_url": "https://bitbucket.org",
    "commits": [
        {
            "author": "marcus",
            "branch": "master",
            "files": [
                {
                    "file": "somefile.py",
                    "type": "modified"
                }
            ],
            "message": "Added some more things to somefile.py",
            "node": "620ade18607a",
            "parents": [
                "702c70160afc"
            ],
            "raw_author": "Marcus Bertrand <marcus@somedomain.com>",
            "raw_node": "620ade18607ac42d872b568bb92acaa9a28620e9",
            "revision": null,
            "size": -1,
            "timestamp": "2012-05-30 05:58:56",
            "utctimestamp": "2012-05-30 03:58:56+00:00"
        }
    ],
    "repository": {
        "absolute_url": "/marcus/project-x/",
        "fork": false,
        "is_private": true,
        "name": "Project X",
        "owner": "marcus",
        "scm": "hg",
        "slug": "project-x",
        "website": "https://atlassian.com/"
    },
    "user": "marcus"
}"""

gitJsonNoCommitsPayload = b"""{
    "canon_url": "https://bitbucket.org",
    "commits": [
    ],
    "repository": {
        "absolute_url": "/marcus/project-x/",
        "fork": false,
        "is_private": true,
        "name": "Project X",
        "owner": "marcus",
        "scm": "git",
        "slug": "project-x",
        "website": "https://atlassian.com/"
    },
    "user": "marcus"
}"""

mercurialJsonNoCommitsPayload = b"""{
    "canon_url": "https://bitbucket.org",
    "commits": [
    ],
    "repository": {
        "absolute_url": "/marcus/project-x/",
        "fork": false,
        "is_private": true,
        "name": "Project X",
        "owner": "marcus",
        "scm": "hg",
        "slug": "project-x",
        "website": "https://atlassian.com/"
    },
    "user": "marcus"
}"""


class TestChangeHookConfiguredWithBitbucketChange(TestReactorMixin, unittest.TestCase):
    """Unit tests for BitBucket Change Hook"""

    @defer.inlineCallbacks
    def setUp(self):
        self.setup_test_reactor()
        master = yield fakeMasterForHooks(self)
        self.change_hook = change_hook.ChangeHookResource(
            dialects={'bitbucket': True}, master=master
        )

    @defer.inlineCallbacks
    def testGitWithChange(self):
        change_dict = {b'payload': [gitJsonPayload]}

        request = FakeRequest(change_dict)
        request.received_headers[_HEADER_EVENT] = b"repo:push"
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)

        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 1)
        commit = self.change_hook.master.data.updates.changesAdded[0]

        self.assertEqual(commit['files'], ['somefile.py'])
        self.assertEqual(commit['repository'], 'https://bitbucket.org/marcus/project-x/')
        self.assertEqual(commit['when_timestamp'], 1338350336)
        self.assertEqual(commit['author'], 'Marcus Bertrand <marcus@somedomain.com>')
        self.assertEqual(commit['revision'], '620ade18607ac42d872b568bb92acaa9a28620e9')
        self.assertEqual(commit['comments'], 'Added some more things to somefile.py')
        self.assertEqual(commit['branch'], 'master')
        self.assertEqual(
            commit['revlink'],
            'https://bitbucket.org/marcus/project-x/commits/'
            '620ade18607ac42d872b568bb92acaa9a28620e9',
        )
        self.assertEqual(commit['properties']['event'], 'repo:push')

    @defer.inlineCallbacks
    def testGitWithNoCommitsPayload(self):
        change_dict = {b'payload': [gitJsonNoCommitsPayload]}

        request = FakeRequest(change_dict)
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)

        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 0)
        self.assertEqual(request.written, b'no change found')

    @defer.inlineCallbacks
    def testMercurialWithChange(self):
        change_dict = {b'payload': [mercurialJsonPayload]}

        request = FakeRequest(change_dict)
        request.received_headers[_HEADER_EVENT] = b"repo:push"
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)

        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 1)
        commit = self.change_hook.master.data.updates.changesAdded[0]

        self.assertEqual(commit['files'], ['somefile.py'])
        self.assertEqual(commit['repository'], 'https://bitbucket.org/marcus/project-x/')
        self.assertEqual(commit['when_timestamp'], 1338350336)
        self.assertEqual(commit['author'], 'Marcus Bertrand <marcus@somedomain.com>')
        self.assertEqual(commit['revision'], '620ade18607ac42d872b568bb92acaa9a28620e9')
        self.assertEqual(commit['comments'], 'Added some more things to somefile.py')
        self.assertEqual(commit['branch'], 'master')
        self.assertEqual(
            commit['revlink'],
            'https://bitbucket.org/marcus/project-x/commits/'
            '620ade18607ac42d872b568bb92acaa9a28620e9',
        )
        self.assertEqual(commit['properties']['event'], 'repo:push')

    @defer.inlineCallbacks
    def testMercurialWithNoCommitsPayload(self):
        change_dict = {b'payload': [mercurialJsonNoCommitsPayload]}

        request = FakeRequest(change_dict)
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)

        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 0)
        self.assertEqual(request.written, b'no change found')

    @defer.inlineCallbacks
    def testWithNoJson(self):
        request = FakeRequest()
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)
        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 0)
        self.assertEqual(request.written, b'Error processing changes.')
        request.setResponseCode.assert_called_with(500, b'Error processing changes.')
        self.assertEqual(len(self.flushLoggedErrors()), 1)

    @defer.inlineCallbacks
    def testGitWithChangeAndProject(self):
        change_dict = {b'payload': [gitJsonPayload], b'project': [b'project-name']}

        request = FakeRequest(change_dict)
        request.uri = b'/change_hook/bitbucket'
        request.method = b'POST'

        yield request.test_render(self.change_hook)

        self.assertEqual(len(self.change_hook.master.data.updates.changesAdded), 1)
        commit = self.change_hook.master.data.updates.changesAdded[0]

        self.assertEqual(commit['project'], 'project-name')
