from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from calculadoraAdjudicacion.forms import PlanActualForm, PlanPorAdjudicarForm, AporteActualForm
from .models import PlanActual, PlanPorAdjudicar, ValorActualizado
from decimal import getcontext, Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def index(request):
    return render(request, 'index.html')

def plan_actual(request):
    if request.method == 'POST':
        form = PlanActualForm(request.POST)
        if form.is_valid():
            registro = form.save()
            pk = registro.id
            return HttpResponseRedirect(reverse('proyeccion', args=(pk,)))
        
    else:
        form = PlanActualForm()
    
    return render(request, 'planActual.html', {'form':form})

def proyeccion(request, pk):
    pk = pk
    if request.method == 'POST':
        form = PlanPorAdjudicarForm(request.POST)
        if form.is_valid():
            registro = form.save()
            pk2 = registro.id
            return HttpResponseRedirect(reverse('resultado', args=(pk,pk2,)))
    
    else:
        form = PlanPorAdjudicarForm()
    
    return render(request, 'proyeccion.html', {'form': form,'pk':pk})

def resultado(request, pk, pk2):
    
    # Formateo de valores en pesos para mostrar en template
    miles_conversor = str.maketrans(".,",",.")
    def pesos(valor):
        pesos = '${:,.2f}'.format(valor).translate(miles_conversor) 
        return pesos
    
    
    # Creación del contexto que será utilizado para enviar variables al template
    contexto_render = {}
    
    
    'LLamado a objetos resultantes de formularios anteriores: "Plan Actual (PA)" y "Plan por Adjudicar (PPA)"'
    planactual = get_object_or_404(PlanActual, pk=pk)
    planadjudicar = get_object_or_404(PlanPorAdjudicar, pk=pk2)
    
    contexto_render['planactual'] = planactual
    contexto_render['planadjudicar'] = planadjudicar
    contexto_render['viviendaactualtipologia'] = planactual.vivienda.get_tipologia_display()
    contexto_render['viviendaactualambientes'] = planactual.vivienda.get_ambientes_display()
    contexto_render['viviendaadjudicartipologia'] = planadjudicar.vivienda_adjudicar.get_tipologia_display()
    contexto_render['viviendaadjudicarambientes'] = planadjudicar.vivienda_adjudicar.get_ambientes_display()
    
    
    "Operaciones Auxiliares"
    
    # Estableciendo el nivel de precisión para las operaciones con números decimales:
    getcontext().prec = 10
    
    # Consulta del valor actualizado de la vivienda actual (en PA):
    valor_vivienda_actual = ValorActualizado.objects.filter(
        cod_hzte=planactual.vivienda).latest('fecha_valor').valor_actualizado
    contexto_render['valor_vivienda_actual'] = pesos(valor_vivienda_actual)
    
    # Consulta del valor actualizado de la vivienda elegida (en PPA):
    valor_vivienda_adjudicar = ValorActualizado.objects.filter(
        cod_hzte=planadjudicar.vivienda_adjudicar).latest('fecha_valor').valor_actualizado
    contexto_render['valor_vivienda_adjudicar'] = pesos(valor_vivienda_adjudicar)
    
    # Consulta de puntos promedio necesarios para adjudicar la vivienda elegida (en PPA)
    puntos_p_adjudicar = planadjudicar.vivienda_adjudicar.puntos
    contexto_render['puntos_p_adjudicar'] = puntos_p_adjudicar
    
    # Consulta de puntos ya obtenidos por antigüedad (en PA)
    puntosant = planactual.ptosantiguedad()
    contexto_render['puntosant'] = puntosant
    
    # Cálculo de puntos por aportes
    puntosaportes = 2 * (
        (planactual.cancelado * Decimal(valor_vivienda_actual)) / Decimal(valor_vivienda_adjudicar))
    contexto_render['puntosaportes'] = puntosaportes
    
    # Cálculo puntos máxmos por ODM
    puntos_odm_previos = planadjudicar.odm * 30
    if ((puntosaportes/2) + puntos_odm_previos) > 100:
        puntos_odm_finales = 100 - (puntosaportes/2)  
    else: puntos_odm_finales = puntos_odm_previos
    contexto_render['punto_odm_finales'] = puntos_odm_finales
    
    # Cálculo de puntos totales acumulados
    puntos_totales_previos = puntosant + puntosaportes + puntos_odm_finales
    
    # Cálculo de aportes por promesas de aportes
    puntos_promesas = Decimal(100 * (
        planadjudicar.oferta_efectivo * 2 +
        planadjudicar.oferta_treinta * 1.98 +
        planadjudicar.oferta_sesenta * 1.96 +
        planadjudicar.oferta_noventa * 1.94 +
        planadjudicar.oferta_c_veinte * 1.92 +
        planadjudicar.oferta_c_cincuenta * 1.90 +
        planadjudicar.oferta_c_ochenta * 1.88
        ) / valor_vivienda_adjudicar)
    
    
    # Cálculo de puntos totales y puntos por promesas de aportes
    if (puntos_totales_previos + puntos_promesas) < 270:
        puntos_totales = puntos_totales_previos + puntos_promesas
        puntos_promesas_final = puntos_promesas
    else:
        puntos_totales = Decimal(270)
        puntos_promesas_final = Decimal(270) - puntos_promesas 
    
    
    contexto_render['puntos_totales'] = '{:,.4f}'.format(puntos_totales).translate(miles_conversor)
    contexto_render['puntos_promesas'] = puntos_promesas_final
    
    # Cálculo de puntos restantes
    puntos_pendientes_previo = puntos_p_adjudicar - puntos_totales
    puntos_pendientes = Decimal(max(0,puntos_pendientes_previo))
    contexto_render['puntos_pendientes'] = '{:,.4f}'.format(puntos_pendientes).translate(miles_conversor)
    
    # Cálculo de cuota mensual luego de adjudicar
    cuota_post_adjudicacion = (
        (planadjudicar.odm/100 + planadjudicar.vivienda_adjudicar.gastos_administrativos) *
        valor_vivienda_adjudicar
        )
    contexto_render['cuota_post_adjudicacion'] = pesos(cuota_post_adjudicacion)
    
    
    
    # Implementación del cálculo de los meses necesarios para adjudicar
    def meses(valor):
        meses = (
            ((puntos_pendientes/200) * valor_vivienda_adjudicar)
            /
            (valor - (valor_vivienda_actual * planactual.vivienda.gastos_administrativos)))
        meses_p_adjudicar = round(meses, 0)
        return meses_p_adjudicar
    
    
    if request.method == 'POST':
        
        form_aporteactual = AporteActualForm(request.POST)
        
        if form_aporteactual.is_valid():
            aportemensualactual = form_aporteactual.cleaned_data['aporte_actual']  
            aporteminimo = (planactual.vivienda.gastos_administrativos * valor_vivienda_adjudicar)
            contexto_render['aportemensualactual'] = pesos(aportemensualactual)
            contexto_render['meses'] = meses(aportemensualactual)
            if (aportemensualactual - aporteminimo) <= 0:
                error = ValidationError(_('Debe ser mayor: %(valor)s (gastos administrativos)'),code='min_value',
                            params={'valor': pesos(aporteminimo)})
                form_aporteactual.add_error('aporte_actual', error)    
                meses_error = 'No es posible calcularlos si no especificas un valor correcto como aporte actual'
                contexto_render['meses'] = meses_error
            
    else:
        aportemensualactualdec = (
            (Decimal(0.006) + planactual.vivienda.gastos_administrativos) *
            valor_vivienda_adjudicar
            )
        aportemensualactual = round(aportemensualactualdec, 0)
        form_aporteactual = AporteActualForm(initial={'aporte_actual':aportemensualactual})
        contexto_render['aportemensualactual'] = pesos(aportemensualactual)
        contexto_render['meses'] = meses(aportemensualactual)
    
        
    
    contexto_render['form'] = form_aporteactual 
    
    return render(request, 'resultado.html',contexto_render)

def puntaje(request):
    return render(request, 'sistema_puntaje.html')