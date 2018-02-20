# fec

### Setup instructions
1. pull this repo
1. `mkvirtualenv fec --python $(which python3)`
1. get a FEC API key [here](https://api.data.gov/signup/)
1. email APIinfo@fec.gov and ask them to upgrade you to 120 api calls per minute
1. add the following to your `$VIRTUAL_ENV/bin/postactivate`:
    ```export DJANGO_SETTINGS_MODULE=config.dev.settings
    export fec_DB_NAME=nyt_dev_fec
    export fec_DB_USER=nyt_dev_fec
    export FEC_API_KEY=your-api-key```
1. `pip install requirements.txt`
1. `createuser -s nyt_dev_fec `
1. `createdb -U nyt_dev_fec nyt_dev_fec`
1. `django-admin migrate`

