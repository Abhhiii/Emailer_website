from django.contrib import admin
from django.http import HttpRequest
from .models import Pdfdata, ClassIndex,FactorsByAltitude,Track,PdfForFactor,TrackDocs
from django.contrib.auth.models import User,Group
from django_cron.models import CronJobLog, CronJobLock

# import django_cron

admin.site.site_header = 'GFR Administration'                    
admin.site.index_title = 'Mailer Website'                 
admin.site.site_title = 'Mailer Website'

# Register your models here.


# @admin.register(Emails)

# class EmailsAdmin(admin.ModelAdmin):
#     list_display = ["email"]
    

    
# admin.site.register(Pdfdata)

class ClassIndexAdmin(admin.ModelAdmin):
    list_display = ('classes','one_by_four','one_by_eight','power_adder',)
    list_per_page = 40
    search_fields = ('classes',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(ClassIndex,ClassIndexAdmin)
# admin.site.unregister(django_cron)

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(CronJobLog)
admin.site.unregister(CronJobLock)



class FactorsByAltitudeAdmin(admin.ModelAdmin):
    list_display = ('altitude','factor','offset',)

    def has_add_permission(self, request) :
        return False
    def has_change_permission(self, request, obj=None) :
        return False
admin.site.register(FactorsByAltitude,FactorsByAltitudeAdmin)

class TrackAdmin(admin.ModelAdmin):
    list_display = ('track_name','city','state','altitude','slet',)

    def has_add_permission(self, request) :
        return False
    def has_change_permission(self, request, obj=None) :
        return False


admin.site.register(Track,TrackAdmin)
admin.site.register(PdfForFactor)
admin.site.register(TrackDocs)
