from django.db import models

class Conversations(models.Model):
    session_id = models.TextField()
    user_input = models.TextField()
    bot_response = models.TextField()
    language = models.TextField()
    confidence = models.FloatField(blank=True, null=True)
    intent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'conversations'


class Context(models.Model):
    session_id = models.TextField()
    context_key = models.TextField()
    context_value = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'context'


class Sessions(models.Model):
    session_id = models.TextField(primary_key=True, blank=True, null=True)
    user_name = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    total_messages = models.IntegerField(blank=True, null=True)
    preferred_language = models.TextField(blank=True, null=True)
    settings = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sessions'


class Metrics(models.Model):
    metric_name = models.TextField()
    metric_value = models.TextField()
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'metrics'


class LearningData(models.Model):
    pattern = models.TextField()
    response = models.TextField()
    intent = models.TextField()
    language = models.TextField()
    frequency = models.IntegerField(blank=True, null=True)
    last_used = models.DateTimeField(blank=True, null=True)
    effectiveness_score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'learning_data'

# Create your models here.
