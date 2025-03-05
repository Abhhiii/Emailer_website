from django.db import models



class Pdfdata(models.Model):
    pdf_url= models.URLField(null=True)
    csv_file= models.FileField(upload_to='csv_files/',blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    sent_emails = models.BooleanField(default=False)


class ClassIndex(models.Model):
    classes = models.CharField(max_length=25,verbose_name = 'Class')
    one_by_four = models.CharField(max_length=25,verbose_name= '1/4 Mile')
    one_by_eight = models.CharField(max_length=25,verbose_name= '1/8 Mile')
    power_adder = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural = 'Class Index'


    def __str__(self):
        return self.classes

    


class Track(models.Model):
    # division = models.CharField(max_length=25,blank=True,null=True)
    # date =  models.CharField(max_length=25,blank=True,null=True)
    track_name = models.CharField(max_length=250,blank=True,null=True)
    city = models.CharField(max_length=250,blank=True,null=True)
    state = models.CharField(max_length=250,blank=True,null=True)
    altitude = models.CharField(max_length=250,blank=True,null=True)
    slet = models.CharField(max_length=250,blank=True,null=True)

    class Meta:
        verbose_name_plural = 'Track List'




class FactorsByAltitude(models.Model):
    altitude = models.CharField(max_length=30,blank=True,null=True)
    factor = models.CharField(max_length=30,blank=True,null=True)
    offset = models.CharField(max_length=30,blank=True,null=True)

    class Meta:
        verbose_name_plural = 'Altitude,Factor and Offset List'
    


class PdfForFactor(models.Model):
    factor_pdf = models.FileField(upload_to="pdf_parser/factor/")

    class Meta:
        verbose_name_plural = 'Upload PDF for altitude details'


class TrackDocs(models.Model):
    track_doc = models.FileField(upload_to="pdf_parser/tracklist/")

    class Meta:
        verbose_name_plural = 'Upload Docx file for Track details'