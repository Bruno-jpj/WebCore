# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

# model for every API-Call
# in case of events such as errors, missing data, etc.. or saving all and deleting after x days


class ApiKeys(models.Model):
    id = models.BigAutoField(primary_key=True)
    header = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'api_keys'


class ApiRequestLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    endpoint = models.CharField(max_length=255)
    payload = models.JSONField()
    response_status = models.IntegerField()
    created_at = models.DateTimeField()
    api = models.ForeignKey(ApiKeys, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_request_logs'


class CoreRequestLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    endpoint = models.CharField(max_length=255)
    payload = models.JSONField()
    response_status = models.IntegerField()
    created_at = models.DateTimeField()
    api = models.ForeignKey(ApiKeys, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'core_request_logs'