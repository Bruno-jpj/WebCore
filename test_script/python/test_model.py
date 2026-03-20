from django.db import models

class TESTAllarmiSoluzioni(models.Model):
    id = models.BigAutoField(primary_key=True)
    titolo = models.CharField(unique=True, max_length=255)
    text_it = models.TextField()
    text_eng = models.TextField()
    text_esp = models.TextField(blank=True, null=True)
    text_de = models.TextField(blank=True, null=True)
    text_fr = models.TextField(blank=True, null=True)
    text_dk = models.TextField(blank=True, null=True)
    text_pt = models.TextField(blank=True, null=True)
    text_ru = models.TextField(blank=True, null=True)
    text_pl = models.TextField(blank=True, null=True)
    text_no = models.TextField(blank=True, null=True)
    text_se = models.TextField(blank=True, null=True)
    img = models.ImageField(upload_to="images/", max_length=255, blank=True, null=True)
    video = models.FileField(upload_to="videos/", max_length=255, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'TEST_allarmi_soluzioni'