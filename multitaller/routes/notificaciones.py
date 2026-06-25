"""
Rutas para el sistema de notificaciones
"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Notificacion, Orden, Contrato, Pieza

notificaciones_bp = Blueprint('notificaciones', __name__)


def crear_notificacion_automatica(tipo, titulo, mensaje, usuario_id=None, enlace=None):
    """
    Crea una notificación automática del sistema.
    
    Args:
        tipo: Tipo de notificación (info, success, warning, danger)
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        usuario_id: ID del usuario (por defecto todos los admins)
        enlace: URL opcional para redireccionar
    """
    if usuario_id:
        # Notificación para un usuario específico
        notificacion = Notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            enlace=enlace
        )
        db.session.add(notificacion)
    else:
        # Notificación para todos los usuarios admin
        from multitaller.models import Usuario
        admins = Usuario.query.filter_by(rol='admin', activo=True).all()
        for admin in admins:
            notificacion = Notificacion(
                usuario_id=admin.id,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                enlace=enlace
            )
            db.session.add(notificacion)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creando notificación: {e}")


def verificar_y_crear_notificaciones():
    """Verifica condiciones y crea notificaciones automáticas"""
    # 1. Órdenes próximas a vencer
    ordenes_proximas = Orden.query.filter(
        Orden.estado_general.notin_(['Completado', 'Cancelado']),
        Orden.fecha_entrega_prevista <= datetime.utcnow() + timedelta(days=2),
        Orden.fecha_entrega_prevista >= datetime.utcnow()
    ).all()
    
    for orden in ordenes_proximas:
        # Verificar si ya existe notificación para esta orden
        existente = Notificacion.query.filter_by(
            titulo=f'Orden {orden.numero_orden} próxima a entregar'
        ).first()
        
        if not existente:
            crear_notificacion_automatica(
                tipo='warning',
                titulo=f'Orden {orden.numero_orden} próxima a entregar',
                mensaje=f'La orden de {orden.cliente.nombre_completo} debe entregarse en menos de 48 horas.',
                enlace=url_for('ordenes.detalle_orden', orden_id=orden.id)
            )
    
    # 2. Piezas con stock bajo
    piezas_bajo_stock = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).all()
    
    for pieza in piezas_bajo_stock:
        existente = Notificacion.query.filter_by(
            titulo=f'Stock bajo: {pieza.nombre}'
        ).first()
        
        if not existente:
            crear_notificacion_automatica(
                tipo='danger',
                titulo=f'Stock bajo: {pieza.nombre}',
                mensaje=f'La pieza {pieza.nombre} tiene solo {pieza.cantidad} unidades disponibles.',
                enlace=url_for('inventario.listar_piezas')
            )
    
    # 3. Contratos próximos a vencer
    contratos_proximos = Contrato.query.filter(
        Contrato.activo == True,
        Contrato.fecha_fin != None,
        Contrato.fecha_fin <= datetime.utcnow() + timedelta(days=7)
    ).all()
    
    for contrato in contratos_proximos:
        existente = Notificacion.query.filter_by(
            titulo=f'Contrato próximo a vencer'
        ).filter(
            Notificacion.mensaje.like(f'%{contrato.cliente.nombre_completo}%')
        ).first()
        
        if not existente:
            crear_notificacion_automatica(
                tipo='warning',
                titulo=f'Contrato próximo a vencer',
                mensaje=f'El contrato de {contrato.cliente.nombre_completo} vence en menos de 7 días.',
                enlace=url_for('contratos.detalle_contrato', contrato_id=contrato.id)
            )


@notificaciones_bp.route('/notificaciones')
@login_required
def listar_notificaciones():
    """Lista todas las notificaciones del usuario actual"""
    # Verificar y crear notificaciones automáticas
    verificar_y_crear_notificaciones()
    
    # Obtener notificaciones del usuario
    notificaciones_usuario = Notificacion.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Notificacion.fecha_creacion.desc()).limit(50).all()
    
    return render_template('notificaciones/listar.html', 
                         notificaciones=notificaciones_usuario)


@notificaciones_bp.route('/notificaciones/marcar_leida/<int:id>', methods=['POST'])
@login_required
def marcar_leida(id):
    """Marca una notificación como leída"""
    notificacion = Notificacion.query.get_or_404(id)
    
    # Solo el dueño de la notificación puede marcarla como leída
    if notificacion.usuario_id != current_user.id:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    notificacion.leida = True
    db.session.commit()
    
    return jsonify({'success': True})


@notificaciones_bp.route('/notificaciones/marcar_todas_leidas', methods=['POST'])
@login_required
def marcar_todas_leidas():
    """Marca todas las notificaciones del usuario como leídas"""
    Notificacion.query.filter_by(
        usuario_id=current_user.id,
        leida=False
    ).update({'leida': True})
    db.session.commit()
    
    return jsonify({'success': True})


@notificaciones_bp.route('/notificaciones/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_notificacion(id):
    """Elimina una notificación"""
    notificacion = Notificacion.query.get_or_404(id)
    
    # Solo el dueño de la notificación puede eliminarla
    if notificacion.usuario_id != current_user.id:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    db.session.delete(notificacion)
    db.session.commit()
    
    return jsonify({'success': True})


@notificaciones_bp.route('/api/notificaciones/count')
@login_required
def contar_no_leidas():
    """API para contar notificaciones no leídas"""
    count = Notificacion.query.filter_by(
        usuario_id=current_user.id,
        leida=False
    ).count()
    
    return jsonify({'count': count})


@notificaciones_bp.route('/api/notificaciones/list')
@login_required
def api_listar_notificaciones():
    """API para listar notificaciones recientes no leídas"""
    notificaciones = Notificacion.query.filter_by(
        usuario_id=current_user.id,
        leida=False
    ).order_by(Notificacion.fecha_creacion.desc()).limit(10).all()
    
    return jsonify({
        'notificaciones': [n.to_dict() for n in notificaciones],
        'total': len(notificaciones)
    })
