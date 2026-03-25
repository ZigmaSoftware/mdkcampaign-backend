from django.apps import AppConfig

class VolunteersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.volunteers'


from django.apps import AppConfig

class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.campaigns'


from django.apps import AppConfig

class ElectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.elections'


from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.analytics'
