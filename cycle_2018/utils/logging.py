import sys
from datadog import initialize, api


def log(title, text="", tags=[]):
    try:
        api.Event.create(title=title,
                    text=text,
                    tags=tags)
    except api.exceptions.ApiNotInitialized:
        pass
    #for now at least we're gonna write everything to stdout
    message = "{}: {}.".format(title, text)
    if tags:
        message += "\nTAGS: {}".format(', '.join(tags))
    message += "\n\n"
    sys.stdout.write(message)


