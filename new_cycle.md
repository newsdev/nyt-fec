# Updating the app for a new cycle

## Background

Before discussing exactly what needs to be done, let's start with a bit of background about the multi-cycle structure and why those decisions were made. We've decided that inside the django project `nyt-fec ` there will be an app for each election cycle called `cycle_YYYY` for the relevant election year ending the two-year period.

Since each app is basically an exact copy of the previous one, you might wonder, why don't we then reuse more code? We decided against that approach because too much changes both in terms of FEC formats and our internal priorities. We do not want to have to maintain backwards compatibility in either of these cases, as doing so might require extensive data migrations on a cycle that is already complete, or break the front-end on a site we rarely check. So we've decided to basically archive each app in time as the cycle ends. This will probably require a few instances of irritating code-copying or some pain should we ever want to do a major cross-cycle comparison. But we think it is the lesser demand compared to having to think possibly several cycles back with every loader or model change.

There are some exceptions to the idea that every cycle is completely segregated. The templates are stored in a top-level directory, although they are mostly cycle-specific, there are some generic ones, including the site index and possibly more tk. In addition, we've decided to put the donor model into its own app. Donors stick around for many cycles, and we think that the ability to match manually-curated donors back in time is valuable.

So why not template or macro this switch out? One reason we're doing this whole copy over deal is because we don't know how our needs or the FEC data will change. So if I carefully wrote default templates for everything this time around, I'd be sure to miss something new next time. Anyway, here goes


## Rolling over

1. Recommended: Squash migrations.
1. Create a new directory for the new cycle, and name it cycle_YYYY (where YYYY is the election year eg 2018)
1. Copy over the contents of the most recent previous cycle.
1. Change every hard-coded instance of the cycle year. You can find-and-replace but I would recommend checking each instance before actually making the change. You'll also need to change some filenames. Here's a (probably not totally complete) list of places you'll need to change the year:  
   * The CYCLE in `cycle_settings.py`
   * The titles of all management commands (django currently overwrites management commands if there are two with the same name even in different apps so we have to prevent that)
   * In import statements in almost all files
   * In `dependencies ` in all migrations (even if sqashed)
   * In any url reverses in `views.py`
   * In any reverse reference to a donor's contributions
   * In the donor model, add fields for the next cycle contributions and make sure they are updated in `save()`
1. In `settings.py` add the new app in `INSTALLED_APPS`
1. In `templates`, copy over the previous cycle's folder and rename for the new cycle
1. Inside each template file, update the date prefix for any forms/actions and the namespace for url reverses
1. In `templates/index.html`, add a link for this cycle
1. In `urls.py`, include the new cycle's urls in `urlpatterns`
1. Update the urls in the base template to point to the current cycle (or change this behavior, I am not tied to it)

## 2016
2016's campfin app is entirely irrelevant software and is maintained in read-only mode.