from django.apps import AppConfig

class VotersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.voters'
    
class VolunteersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.volunteers'
    
class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.campaigns'
    
class ElectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.elections'
    
class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_os.analytics'
