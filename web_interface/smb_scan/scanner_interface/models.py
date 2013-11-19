# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models

class Files(models.Model):
    lid = models.ForeignKey('Shares', null=True, db_column='lid', blank=True, on_delete=models.CASCADE)
    filename = models.CharField(max_length=512)
    fid = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'files'

class Permissions(models.Model):
    uid = models.ForeignKey('Users', db_column='uid', on_delete=models.CASCADE)
    permission = models.CharField(max_length=25)
    fid = models.ForeignKey(Files, db_column='fid', on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'permissions'

class Shares(models.Model):
    server = models.CharField(max_length=255)
    share = models.CharField(max_length=256)
    lid = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'shares'

class Users(models.Model):
    domain = models.CharField(max_length=64)
    username = models.CharField(max_length=64)
    uid = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'users'

