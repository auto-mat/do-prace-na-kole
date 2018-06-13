
class StaleSyncMixin():

    def get_fieldsets(self, request, obj=None):
        #  Move last_sync_time to the end
        res = super().get_fieldsets(request, obj)
        res[0][1]['fields'].append(res[0][1]['fields'].pop(0))
        return res
