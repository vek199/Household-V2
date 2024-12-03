from celery import Celery
from celery.schedules import crontab


  # app.config['CELERY_BROKER_URL'] = 'rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>?ssl_cert_reqs=required'
    # app.config['CELERY_RESULT_BACKEND'] = 'rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/0?ssl_cert_reqs=required'
    
# celery = Celery(__name__,broker='rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>?ssl_cert_reqs=required',backend='rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/0?ssl_cert_reqs=required')
    
celery = Celery(__name__,broker='redis://localhost:6379/0',backend='redis://localhost:6379/0')

CELERY_BEAT_SCHEDULE ={
    'generate_monthly_report':{
        'task':'tasks.generate_monthly_report',
        'schedule':5.0
            #    'schedule':crontab(day_of_month=1)
    },
    'daily_reminders':{
        'task':'tasks.daily_reminders',
        'schedule':11.0
            #    'schedule':crontab(hour=18)

    }
}

#wget https://github.com/mailhog/MailHog/releases/latest/download/mailhog_linux_amd64

celery.conf.beat_schedule = CELERY_BEAT_SCHEDULE