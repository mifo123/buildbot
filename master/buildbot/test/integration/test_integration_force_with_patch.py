    @defer.inlineCallbacks
            yield self.patch(patch)
        return SUCCESS
        build = yield self.doForceBuild(wantSteps=True, wantLogs=True,
                                        forceParams={'foo_patch_body': PATCH})