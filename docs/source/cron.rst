Cron Jobs
-----------------


A number of critical InPhO functions on inpho.cogs are managed by cron through the inpho user account.  The inpho crontab can be edited with ``crontab -e`` or listed with ``crontab -l``. On Mac OS X, the inpho crontab is kept at ``/usr/lib/cron/tabs/inpho`` but should not be edited directly.

Cron jobs:

1.  ``/Users/inpho/bin/do_mirror``, runs at 03:30 each day
    Creates a full mirror of the SEP on inpho.cogs.

2. ``/Users/inpho/bin/data_mining``, runs at 04:00 daily
   Calculates association weights across SEP corpus.

3. ``/Users/inpho/mniepert/dlv/asp-cron.sh``, runs at 03:00 daily
   Runs answer set program to repopulate taxonomy based on current data.

4. ``/Users/inpho/mniepert/cron.sh``, runs hourly
   Updates local list of published entries on SEP.

5. ``/Users/inpho/bin/owl-cron.sh``, runs at 01:00 on the first of every month
   Creates the OWL archive and updates the corresponding web page

6. ``/Users/inpho/bin/backupsep.py``, runs at 05:00 every Sunday morning
   Creates a weekly tar archive of the SEP entries so that we can rerun stats at a later date if required.

7. ``/Users/inpho/bin/checkurl.sh``, runs at midnight every Friday
   Checks URLs in journals database.

8. ``/Users/inpho/bin/fuzzymatch``, runs at 07:00 daily
   Syncs the fuzzymatches daily

9. ``/Users/inpho/bin/sitestats``, runs at the top of every hour
   Updates site statistics
