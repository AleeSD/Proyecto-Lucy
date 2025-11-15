from django.contrib import admin
from .models import Conversations, Context, Sessions, Metrics, LearningData

admin.site.register(Conversations)
admin.site.register(Context)
admin.site.register(Sessions)
admin.site.register(Metrics)
admin.site.register(LearningData)

# Register your models here.
