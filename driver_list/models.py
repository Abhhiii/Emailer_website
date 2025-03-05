from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.



class DriverList(models.Model):
    lic = models.CharField(max_length=25)
    driver = models.CharField(max_length=50)
    classes = models.CharField(max_length=25,verbose_name='Class')
    personal_index = models.CharField(max_length=25)
    # date = models.CharField(max_length=25,null=True,blank=True)




class NewRaceDriversList(models.Model):
    session_id = models.CharField(max_length=255,null=True) 
    type = models.CharField(max_length=25)
    lic = models.CharField(max_length=25,null=True,blank=True)
    driver = models.CharField(max_length=50,null=True,blank=True)
    classes = models.CharField(max_length=25,verbose_name='Class',null=True,blank=True)
    index = models.CharField(max_length=25,null=True,blank=True)
    updated_index = models.CharField(max_length=25,null=True,blank=True)
    # created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)


class UpdatedIndex(models.Model):
    lic = models.CharField(max_length=25)
    driver = models.CharField(max_length=50)
    classes = models.CharField(max_length=25,verbose_name='Class')
    personal_index = models.CharField(max_length=25)
