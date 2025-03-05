from django.contrib import admin
from .models import*
# Register your models here.

# class NewRaceDriversListAdmin(admin.ModelAdmin):
#     list_display=('session_id','lic','driver','classes','index',)
#     search_fields =('lic','driver','classes',)

#     def has_add_permission(self, request):
#         return False

#     # def has_delete_permission(self, request, obj=None):
#     #     return False
    
#     def has_change_permission(self, request, obj=None):
#         return False
    
admin.site.register(NewRaceDriversList)
class IndexAdmin(admin.ModelAdmin):
    list_display = ('lic','driver','classes','personal_index',)
    list_per_page = 52
admin.site.register(DriverList,IndexAdmin)
class UpdatedIndexAdmin(admin.ModelAdmin):
    list_display = ('lic','driver','classes','personal_index',)
    list_per_page = 52
admin.site.register(UpdatedIndex,UpdatedIndexAdmin)