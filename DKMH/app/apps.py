from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
<<<<<<< HEAD
    def ready(self):
        import app.signals  
=======
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64
