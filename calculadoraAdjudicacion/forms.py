from django.forms import ModelForm,ModelChoiceField
from django import forms
from calculadoraAdjudicacion.models import PlanActual, PlanPorAdjudicar
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ViviendaActualChoiceField(ModelChoiceField):
        def label_from_instance(self, obj):
            return obj.cod_hzte

class PlanActualForm (ModelForm):
    class Meta:
        model = PlanActual
        exclude = ['deuda']
        field_classes = {
            'vivienda': ViviendaActualChoiceField
        }
    
    def clean_cancelado(self):
        data = self.cleaned_data['cancelado']
        if data > 100:
            raise ValidationError(_('No puedes indicar un porcentaje mayor al 100%'))
        if data <= 0:
            raise ValidationError(_('Debes indicar un porcentaje mayor a 0%'))
        return data

class PlanPorAdjudicarForm(ModelForm):
    def clean_odm(self):
        data = self.cleaned_data['odm']
        if data > 1 or data < 0.84:
            raise ValidationError(_('El porcentaje debe estar entre 0,84% y 1%'))
        return data
    
    class Meta:
        model = PlanPorAdjudicar
        fields = '__all__'

class AporteActualForm(forms.Form):
    aporte_actual = forms.DecimalField(
        # label='Aporte mensual (antes de adjudicar)',
        # help_text='Monto mensual a aportar hasta el momento de la adjudicación',
        min_value=1,
        max_digits=8,
        decimal_places=2
        )