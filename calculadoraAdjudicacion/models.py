from django.db import models
from _datetime import date
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

'''
Definición de "Vivienda", representación de los tipos de viviendas elegibles.
Tipos de viviendas: resultado de combinaciones de tipología, tamaño de lote y cantidad de ambientes/dormitorios.
Los tipos de viviendas están pre-tabulados por la Cooperativa Horizonte Ltda.
'''
class Vivienda(models.Model):
    
    # Código de identificacion Vivienda Elegible según nomenclador de Horizonte
    cod_hzte = models.CharField(
        "codigo horizonte", 
        max_length=6, 
        unique=True
    )
    
    # Definición de 'choices' de tipologías que serán referenciadas en la definición del campo 'tipología'
    class TiposDisponibles(models.TextChoices):
        COMPACTA = 'E', _('Compacta')
        BASICA = 'D', _('Basica')
        ECONOMICA = 'C', _('Economica')
        ECONOMICAESQ = 'CE', _('Economica en esquina')
        STANDARD = 'B', _('Standard')
        STANDARDESQ = 'BE', _('Standar en esquina')
        MEJORADA = 'A', _('Mejorada')
    tipologia = models.CharField(max_length=2,choices=TiposDisponibles.choices)
    
    # Tamaño de lote
    class Lotes(models.TextChoices):
        ESTANDAR = 'LE', _('Tamaño estandar')
        AMPLIADO = 'LAM', _('Tamaño ampliado')
    lote = models.CharField(max_length=3,choices=Lotes.choices,default=Lotes.ESTANDAR)
    
    # Definición de cantidad de ambientes de la vivienda
    class Ambientes(models.TextChoices):
        MONO = 'MO', _('Monoambiente')
        UNO = '01', _('1 Dormitorio')
        DOS = '02', _('2 Dormitorios')
        TRES = '03', _('3 Dormitorios')
    ambientes = models.CharField(max_length=2,choices=Ambientes.choices)
    
    # Define si la vivienda está disponible actualmente para ser adjudicada
    vigente = models.BooleanField(default=True)
    
    '''
    Campo que representa la sumatoria de Gastos Administrativos y 'AMAC'
    Valor expresado en términos del valor de la Vivienda
    '''
    gastos_administrativos = models.DecimalField(
        max_digits=7, 
        decimal_places=6,
        default=0.000700
    )

    '''
    Campo que indica los puntos obtenidos por los socios al momento de adjudicar la vivienda
    Es un promedio de los puntos obtenidos por todos los socios que adjudicaron la vivienda "X"
    '''
    puntos = models.DecimalField(
        max_digits=7, 
        decimal_places=4,
        verbose_name="puntos para adjudicar"
    )
    
    # String para representar al objeto 'Vivienda'
    def __str__(self):
        if self.lote == 'LE':
            return '{0} - {1}'.format(self.get_tipologia_display(),self.get_ambientes_display())
        else:
            return '{0} - {1} ({2})'.format(self.get_tipologia_display(),self.get_ambientes_display(),self.lote)
    

'''
Definición "ValorActualizado", representación del valor actualizado de la 'Vivienda'.
'''
class ValorActualizado(models.Model):
    cod_hzte = models.ForeignKey(
        Vivienda,
        to_field='cod_hzte',
        on_delete=models.SET_NULL,
        null=True
    )
    fecha_valor = models.DateField(default=date.today())
    valor_actualizado = models.PositiveIntegerField()
    
    def __str__(self):
        miles_conversor = str.maketrans(".,",",.")
        codigo = '{}'.format(self.cod_hzte)
        monto = '${:,.2f}'.format(self.valor_actualizado).translate(miles_conversor)
        periodo = self.fecha_valor.strftime("%b") + '/' + self.fecha_valor.strftime("%Y") 
        return periodo + ' [' + codigo + ']' + ' ' + monto

'''
Definición del "Plan Actual", representación del estado del plan al que actualmente está aportando
el usuario-
'''
class PlanActual(models.Model):
    # Vivienda a la que aporta
    vivienda = models.ForeignKey(
        Vivienda,
        to_field='cod_hzte',
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Antiguedad en el plan (será definida en meses)
    antiguedad = models.PositiveIntegerField(blank=False)
    
    # Porcentaje cancelado de la vivienda a la que aporta actualmente
    cancelado = models.DecimalField(
        max_digits=7, 
        decimal_places=4, 
        blank=False,
    )
    
    # Deuda por gastos administrativos
    deuda = models.PositiveIntegerField(default=0)
    
    # Cálculo de puntos por antigüedad en el plan
    def ptosantiguedad(self):
        # Cálculo preliminar según sistema de puntaje
        puntos_calculados = self.antiguedad*1.5
        # Definición del puntaje final, considerando que existe un tope de puntos por antigüedad de 70 ptos.
        puntos_ant = min(70, puntos_calculados)
        
        ptosantiguedad = Decimal(puntos_ant)
        return ptosantiguedad


'''
Definición del "Plan a adjudicar", representación del plan que proyecta adjudicar el usuario.
'''        
class PlanPorAdjudicar(models.Model):
    # Vivienda que proyecta adjudicar (puede, o no, coincidir con la vivienda correspondiente al plan actual
    vivienda_adjudicar = models.ForeignKey(
        Vivienda,
        # to_field='cod_hzte',
        limit_choices_to={'vigente': True},
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    
    # Oferta de Devolución mensual (en %)
    odm = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        default=0.84
    )
    
    # Ofertas de aporte en efectivo que complementan la postulación que el usuario proyecta realizar
    oferta_efectivo = models.PositiveIntegerField(default=0)
    oferta_treinta = models.PositiveIntegerField(default=0)
    oferta_sesenta = models.PositiveIntegerField(default=0)
    oferta_noventa = models.PositiveIntegerField(default=0)
    oferta_c_veinte = models.PositiveIntegerField(default=0)
    oferta_c_cincuenta = models.PositiveIntegerField(default=0)
    oferta_c_ochenta = models.PositiveIntegerField(default=0)
    
    