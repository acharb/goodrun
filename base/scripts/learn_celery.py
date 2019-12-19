from celery import Celery

# create instance of celery
# entry point for everything celery (creating tasks, managing workers), so it must be possible for other modules to import

celery = Celery('<current module>', backend='<URL of result_backend (optional)>', broker='<URL of message broker you want to use>' )


# Run the celery worker server (using 'worker' argument)
$ celery -A tasks worker --loglevel=info


# in production, need to run worker in the background as a 'dameon'

# for help
$  celery worker --help



# FOR LARGER PROJECTS, using a config module is recommended
# configure celery instance from you settings file
# broker setup in settings
celery.config_from_object('django.conf:settings')