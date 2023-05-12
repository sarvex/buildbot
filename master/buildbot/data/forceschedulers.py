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

from buildbot.data import base
from buildbot.data import types
from buildbot.schedulers import forcesched
from buildbot.www.rest import JSONRPC_CODES
from buildbot.www.rest import BadJsonRpc2


def forceScheduler2Data(sched):
    ret = dict(all_fields=[],
               name=str(sched.name),
               button_name=str(sched.buttonName),
               label=str(sched.label),
               builder_names=[str(name)
                              for name in sched.builderNames],
               enabled=sched.enabled)
    ret["all_fields"] = [field.getSpec() for field in sched.all_fields]
    return ret


class ForceSchedulerEndpoint(base.Endpoint):

    isCollection = False
    pathPatterns = """
        /forceschedulers/i:schedulername
    """

    def findForceScheduler(self, schedulername):
        return next(
            (
                defer.succeed(sched)
                for sched in self.master.allSchedulers()
                if sched.name == schedulername
                and isinstance(sched, forcesched.ForceScheduler)
            ),
            None,
        )

    @defer.inlineCallbacks
    def get(self, resultSpec, kwargs):
        sched = yield self.findForceScheduler(kwargs['schedulername'])
        return forceScheduler2Data(sched) if sched is not None else None

    @defer.inlineCallbacks
    def control(self, action, args, kwargs):
        if action == "force":
            sched = yield self.findForceScheduler(kwargs['schedulername'])
            if "owner" not in args:
                args['owner'] = "user"
            try:
                return (yield sched.force(**args))
            except forcesched.CollectedValidationError as e:
                raise BadJsonRpc2(e.errors, JSONRPC_CODES["invalid_params"]) from e
        return None


class ForceSchedulersEndpoint(base.Endpoint):

    isCollection = True
    pathPatterns = """
        /forceschedulers
        /builders/:builderid/forceschedulers
    """
    rootLinkName = 'forceschedulers'

    @defer.inlineCallbacks
    def get(self, resultSpec, kwargs):
        builderid = kwargs.get('builderid', None)
        if builderid is not None:
            bdict = yield self.master.db.builders.getBuilder(builderid)
        return [
            forceScheduler2Data(sched)
            for sched in self.master.allSchedulers()
            if isinstance(sched, forcesched.ForceScheduler)
            and (builderid is None or bdict['name'] in sched.builderNames)
        ]


class ForceScheduler(base.ResourceType):

    name = "forcescheduler"
    plural = "forceschedulers"
    endpoints = [ForceSchedulerEndpoint, ForceSchedulersEndpoint]
    keyField = "name"

    class EntityType(types.Entity):
        name = types.Identifier(50)
        button_name = types.String()
        label = types.String()
        builder_names = types.List(of=types.Identifier(50))
        enabled = types.Boolean()
        all_fields = types.List(of=types.JsonObject())
    entityType = EntityType(name, 'Forcescheduler')
