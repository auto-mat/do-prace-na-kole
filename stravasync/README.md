The stravasync django app
-------------------------

The stravasync app allows you to synchronize the do-prace-na-kolo ride table with Strava. This is a one way import from strava, and does not upload any activities to strava. The app contains a configuration screen in which the user can connect to their Strava account and force a synchronization. Synchronizations can also be scheduled for all user's with linked Strava accounts using the sync_stale celery task.

Configuration
-------------

Set the following variables in your project settings.

````
STRAVA_CLIENT_ID="foobar"
STRAVA_CLIENT_SECRET="bafbazboo"
STRAVA_FINE_POLYLINES = True
STRAVA_MAX_USER_SYNC_COUNT = 16
````

The `STRAVA_FINE_POLYLINES` variable sets whether stravasync should get a higher quality version of activity routes, at the expense of one extra API request per activity.

The `STRAVA_MAX_USER_SYNC_COUNT` determines how many times a given user is allowed to manually request a sync with Strava. This is to prevent DOS scenarios where a user exhausts the Strava API request limit by manually syncing many times.

In django admin
---------------

In django admin add several instances of the periodic task stravasync.tasks.sync_stale.

Pass the keyword arguments:

````
{
"min_time_between_syncs":43200,
"max_batch_size":300
}
````
