# fec

## Note!

**VERSION 1.1 INCLUDES BREAKING CHANGES THAT COULD LEAD TO DATA LOSS!** The previous working version is tagged `working`
If you would like to update to the current version, which supports multiple cycles, and you have data in your donors table, please update to v1.0, run the sql updates described [here](https://github.com/newsdev/nyt-fec/issues/63), and then go up to v1.1. Also strongly recommended to backup your whole database before doing any of this.

App is still kind of in the scratchpad phase, absolutely no promises that it works or I won't make breaking changes.

## About
This app allows for importing and searching expenditures, independent expenditures and contributions from electronic FEC filings. It relies on the NYT's [fec2json](https://github.com/newsdev/fec2json) library.

#### Why not just use the FEC website? 
The FEC website has been substantially improved recently, but it still lacks several main features we desire.
1. It takes several days for itemizations to be processed, so it is impossible to search transactions right away
1. There are some search fields that are important to me that do not exist in the FEC
1. We want to be able to do more with independent expenditure summing and categorizing
1. We want to be able to add additional data, such as our own donor ids

If you don't *really* need to deploy and maintain your own standalone campaign finance infrastructure, however, I recommend using tools developped by the FEC including their [site](https://www.fec.gov/data/?search=), their [api](https://api.open.fec.gov/developers/) or their [bulk data](https://classic.fec.gov/finance/disclosure/ftp_download.shtml). Or use ProPublica's [site](https://projects.propublica.org/itemizer/) or [api](https://www.propublica.org/datastore/api/campaign-finance-api).

### Setup instructions
1. pull this repo
1. `mkvirtualenv fec --python $(which python3)`
1. get a FEC API key [here](https://api.data.gov/signup/)
1. email APIinfo@fec.gov and ask them to upgrade you to 120 api calls per minute
1. add the following to your `$VIRTUAL_ENV/bin/postactivate`:
    ```bash
    export DJANGO_SETTINGS_MODULE=config.dev.settings
    export fec_DB_NAME=nyt_dev_fec
    export fec_DB_USER=nyt_dev_fec
    export FEC_API_KEY=your-api-key
    ```
1. `pip install -r requirements.txt`
1. `createuser -s nyt_dev_fec `
1. `createdb -U nyt_dev_fec nyt_dev_fec`
1. `add2virtualenv . && add2virtualenv config && add2virtualenv fec`
1. `django-admin migrate`

