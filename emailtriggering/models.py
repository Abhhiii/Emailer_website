from django.db import models

# Create your models here.

class ResendEmail(models.Model):
    resend_email = models.BooleanField(default=False)
    send_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.send_at)




class PreviousTriggeredEmail(models.Model):
    index = models.ForeignKey(ResendEmail,on_delete = models.CASCADE,null=True)
    lic_data = models.CharField(max_length=25)
    driver_data = models.CharField(max_length=25)
    classs_data = models.CharField(max_length=25)
    locationEvent_data = models.CharField(max_length=250)
    date_data = models.CharField(max_length=25)
    mineshaft_data = models.CharField(max_length=25)
    personalIndex_data = models.CharField(max_length=25)
    classIDX_data = models.CharField(max_length=25)
    et_data = models.CharField(max_length=25)
    underPersonalIDX_data = models.CharField(max_length=25)
    newPersonalIDX_data = models.CharField(max_length=25)
    underClassIDX_data = models.CharField(max_length=25)
    newClassIDX_data = models.CharField(max_length=25)


