from django.contrib import admin
import scanner_interface.models as dbmodels

admin.site.register(dbmodels.Files)
admin.site.register(dbmodels.Permissions)
admin.site.register(dbmodels.Shares)
admin.site.register(dbmodels.Users)
