from django.contrib import admin
from emailtriggering.models import*
from django.conf import settings
from pdf_parser.utils import send_payload_to_customer_io_testgroup, create_log_message
import time



# # Register your models here.
class PreviousTriggeredEmailInline(admin.StackedInline): 
    model = PreviousTriggeredEmail
    extra = 0
    readonly_fields=('index','lic_data','driver_data','classs_data','locationEvent_data','date_data','mineshaft_data','personalIndex_data','classIDX_data','et_data','underPersonalIDX_data','newPersonalIDX_data','underClassIDX_data','newClassIDX_data',)

    def has_add_permission(self, request,obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    




class ResendEmailAdmin(admin.ModelAdmin):
    inlines = [PreviousTriggeredEmailInline]
    list_display = ('send_at', 'resend_email')
    list_per_page = 10

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.resend_email:
            try:
                alerts = []
                previous_emails = PreviousTriggeredEmail.objects.filter(index=obj)
                for previous_email in previous_emails:
                    alert_data = {
                        "lic": previous_email.lic_data,
                        "driver": previous_email.driver_data,
                        "class": previous_email.classs_data,
                        "locationEvent": previous_email.locationEvent_data,
                        "date": previous_email.date_data,
                        "mineshaft": previous_email.mineshaft_data,
                        "personalIndex": previous_email.personalIndex_data,
                        "classIDX": previous_email.classIDX_data,
                        "et": previous_email.et_data,
                        "underPersonalIDX": previous_email.underPersonalIDX_data,
                        "newPersonalIDX": previous_email.newPersonalIDX_data,
                        "underClassIDX": previous_email.underClassIDX_data,
                        "newClassIDX": previous_email.newClassIDX_data
                    }
                    alerts.append(alert_data)

                json_data = {'items': alerts}

                payload = {
                    "data": json_data
                }


                api_key = settings.CUSTOMER_IO_API_KEY
                send_payload_to_customer_io_testgroup(api_key=api_key, payload=payload)
                time.sleep(10)

            except Exception as e:
                create_log_message(message=f"Error in sending appended rows email: {str(e)}",properties={"Function": "ResendEmail.save"})

    
admin.site.register(ResendEmail,ResendEmailAdmin)


# class PreviousTriggeredEmailAdmin(admin.ModelAdmin):
#     list_display=('index','lic_data','driver_data','classs_data','locationEvent_data','date_data','mineshaft_data','personalIndex_data','classIDX_data','et_data','underPersonalIDX_data','newPersonalIDX_data','underClassIDX_data','newClassIDX_data',)


# admin.site.register(PreviousTriggeredEmail,PreviousTriggeredEmailAdmin)