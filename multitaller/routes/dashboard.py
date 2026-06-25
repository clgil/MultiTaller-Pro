"""
Blueprint para el dashboard (panel de control)
"""

from flask import Blueprint, render_template, session, request
from datetime import datetime, timedelta, timezone
from models import db, Orden, Pieza, Cliente, Contrato, Gasto, Configuracion

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def index():
    """Panel de control principal"""
    if 'usuario_id' not in session:
        return {'error': 'No autorizado'}, 401
    
    # Obtener período seleccionado
    periodo = request.args.get('periodo', 'mes')
    
    # Calcular fechas del período
    hoy = datetime.now(timezone.utc)
    if periodo == 'hoy':
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'ano':
        fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Contadores de órdenes
    ordenes_activas = Orden.query.filter(
        Orden.estado_general.not_in(['Entregado', 'Cancelado'])
    ).count()
    
    ordenes_pendientes_diagnostico = Orden.query.filter_by(estado_general='En diagnóstico').count()
    ordenes_listas_entregar = Orden.query.filter_by(estado_general='Listo para entregar').count()
    
    # Piezas bajo stock mínimo
    piezas_bajo_stock = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).all()
    
    # Próximos mantenimientos (esta semana)
    proxima_semana = hoy + timedelta(days=7)
    contratos_activos = Contrato.query.filter_by(activo=True).all()
    proximos_mantenimientos = []
    
    for contrato in contratos_activos:
        proximo = contrato.get_proximo_mantenimiento()
        if proximo and hoy <= proximo <= proxima_semana:
            proximos_mantenimientos.append({
                'contrato': contrato,
                'cliente': contrato.cliente,
                'fecha_proxima': proximo
            })
    
    # Garantías próximas a vencer (próximos 15 días)
    proximos_15_dias = hoy + timedelta(days=15)
    garantias_por_vencer = Orden.query.filter(
        Orden.fecha_fin_garantia != None,
        Orden.fecha_fin_garantia >= hoy,
        Orden.fecha_fin_garantia <= proximos_15_dias,
        Orden.estado_general == 'Entregado'
    ).all()
    
    # Últimas 10 órdenes actualizadas
    ultimas_ordenes = Orden.query.order_by(Orden.fecha_creacion.desc()).limit(10).all()
    
    # Panel financiero
    datos_financieros = calcular_panel_financiero(fecha_inicio, hoy)
    
    # Configuración de moneda
    moneda_principal = Configuracion.query.filter_by(clave='moneda_principal').first()
    moneda_secundaria = Configuracion.query.filter_by(clave='moneda_secundaria').first()
    tasa_cambio = Configuracion.query.filter_by(clave='tasa_cambio').first()
    
    return render_template('dashboard/index.html',
                         ordenes_activas=ordenes_activas,
                         ordenes_pendientes_diagnostico=ordenes_pendientes_diagnostico,
                         ordenes_listas_entregar=ordenes_listas_entregar,
                         piezas_bajo_stock=piezas_bajo_stock,
                         proximos_mantenimientos=proximos_mantenimientos,
                         garantias_por_vencer=garantias_por_vencer,
                         ultimas_ordenes=ultimas_ordenes,
                         datos_financieros=datos_financieros,
                         moneda_principal=moneda_principal.valor if moneda_principal else 'CUP',
                         moneda_secundaria=moneda_secundaria.valor if moneda_secundaria else 'MLC',
                         tasa_cambio=float(tasa_cambio.valor) if tasa_cambio else 1.0,
                         periodo=periodo)


def calcular_panel_financiero(fecha_inicio, fecha_fin):
    """Calcula indicadores financieros del período"""
    from sqlalchemy import func
    
    # Ingresos por órdenes entregadas en el período
    ordenes_periodo = Orden.query.filter(
        Orden.fecha_entrega_real >= fecha_inicio,
        Orden.fecha_entrega_real <= fecha_fin,
        Orden.estado_general == 'Entregado'
    ).all()
    
    ingresos_brutos = sum(o.costo_total for o in ordenes_periodo)
    
    # Costo de piezas vendidas (necesitaría una tabla de movimientos más detallada)
    # Por ahora estimamos como 40% de los ingresos (margue típico)
    costo_piezas = ingresos_brutos * 0.4
    
    # Gastos operativos del período
    gastos_operativos_data = Gasto.query.filter(
        Gasto.fecha >= fecha_inicio,
        Gasto.fecha <= fecha_fin
    ).all()
    
    gastos_operativos = sum(g.monto for g in gastos_operativos_data)
    
    # Ganancia neta
    ganancia_neta = ingresos_brutos - costo_piezas - gastos_operativos
    
    # Valor actual del inventario
    piezas = Pieza.query.all()
    valor_inventario = sum(p.cantidad * p.precio_costo for p in piezas)
    
    # Cálculo de tributos
    configuracion = Configuracion.query.filter(
        Configuracion.clave.in_(['regimen_tributario', 'seguridad_social_porcentaje'])
    ).all()
    
    regimen = 'general'
    ss_percentage = 5
    
    for conf in configuracion:
        if conf.clave == 'regimen_tributario':
            regimen = conf.valor
        elif conf.clave == 'seguridad_social_porcentaje':
            ss_percentage = float(conf.valor)
    
    isip_estimado = 0
    seguridad_social = ganancia_neta * (ss_percentage / 100) if ganancia_neta > 0 else 0
    
    if regimen == 'general':
        # Calcular ISIP progresivo
        import json
        isip_tramos_conf = Configuracion.query.filter_by(clave='isip_tramos').first()
        if isip_tramos_conf:
            tramos = json.loads(isip_tramos_conf.valor)
            ganancia_restante = ganancia_neta
            for tramo in sorted(tramos, key=lambda x: x['hasta'] or float('inf')):
                limite = tramo['hasta'] if tramo['hasta'] else ganancia_neta
                if ganancia_restante > 0:
                    monto_tramo = min(ganancia_restante, limite)
                    isip_estimado += monto_tramo * (tramo['porcentaje'] / 100)
                    ganancia_restante -= monto_tramo
    else:
        # Régimen simplificado - cuota fija
        cuota_fija_conf = Configuracion.query.filter_by(clave='cuota_fija_mensual').first()
        if cuota_fija_conf:
            isip_estimado = float(cuota_fija_conf.valor)
    
    return {
        'ingresos_brutos': ingresos_brutos,
        'costo_piezas': costo_piezas,
        'gastos_operativos': gastos_operativos,
        'ganancia_neta': ganancia_neta,
        'valor_inventario': valor_inventario,
        'isip_estimado': isip_estimado,
        'seguridad_social': seguridad_social,
        'total_tributos': isip_estimado + seguridad_social
    }
