from django.contrib import admin
from .models import Vivienda, ValorActualizado, PlanActual, PlanPorAdjudicar
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class ValorActualizadoResource(resources.ModelResource):
    class Meta:
        model = ValorActualizado

class ValorActualizadoAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = ValorActualizadoResource


class ViviendaResource(resources.ModelResource):
    class Meta:
        model = Vivienda

class ViviendaAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('cod_hzte','tipologia','lote','ambientes','vigente','gastos_administrativos')
    resource_class = ViviendaResource


admin.site.register(Vivienda,ViviendaAdmin)
admin.site.register(ValorActualizado,ValorActualizadoAdmin)
admin.site.register(PlanActual)
admin.site.register(PlanPorAdjudicar)