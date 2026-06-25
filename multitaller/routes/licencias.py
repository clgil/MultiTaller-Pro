"""
Blueprint para sistema de licencias y activación
"""

import os
import hmac
import hashlib
import platform
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models import db, Configuracion, Licencia
from routes.auth import login_required, admin_required

licencias_bp = Blueprint('licencias', __name__)

# Clave secreta para generación de licencias (en producción, usar una única clave embebida)
SECRET_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secret.key')


def get_secret_key():
    """Obtiene o genera la clave secreta para licencias"""
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Generar nueva clave
        key = os.urandom(32)
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
        return key


def generar_id_maquina():
    """Genera un ID único basado en el hardware del equipo"""
    # En producción, usar identificadores reales del hardware
    # Para desarrollo, usamos una combinación simple
    node = platform.node()
    processor = platform.processor()
    machine = platform.machine()
    
    datos = f"{node}-{processor}-{machine}"
    return hashlib.sha256(datos.encode()).hexdigest()[:16]


def generar_codigo_activacion(id_maquina, tipo_licencia='estandar'):
    """Genera código de activación usando HMAC-SHA256"""
    secret_key = get_secret_key()
    
    # Datos a firmar
    datos = f"{id_maquina}:{tipo_licencia}"
    
    # Generar firma HMAC
    firma = hmac.new(secret_key, datos.encode(), hashlib.sha256).hexdigest()
    
    # Código final (ID + tipo + firma truncada)
    codigo = f"{id_maquina}-{tipo_licencia}-{firma[:16]}"
    
    return codigo


def validar_codigo_activacion(codigo):
    """Valida un código de activación"""
    try:
        partes = codigo.split('-')
        if len(partes) != 3:
            return False, None
        
        id_maquina = partes[0]
        tipo_licencia = partes[1]
        firma_recibida = partes[2]
        
        # Regenerar firma
        secret_key = get_secret_key()
        datos = f"{id_maquina}:{tipo_licencia}"
        firma_esperada = hmac.new(secret_key, datos.encode(), hashlib.sha256).hexdigest()[:16]
        
        if firma_recibida != firma_esperada:
            return False, None
        
        # Verificar que el ID coincide con el de la máquina actual
        id_actual = generar_id_maquina()
        if id_maquina != id_actual:
            return False, None
        
        return True, tipo_licencia
    
    except Exception as e:
        return False, None


@licencias_bp.route('/activacion', methods=['GET', 'POST'])
def activacion():
    """Pantalla de activación del sistema"""
    if request.method == 'POST':
        codigo = request.form.get('codigo_activacion', '').strip()
        
        if not codigo:
            flash('El código de activación es requerido', 'warning')
            return render_template('licencias/activacion.html')
        
        valido, tipo_licencia = validar_codigo_activacion(codigo)
        
        if valido:
            # Guardar licencia
            license_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'license.dat')
            with open(license_file, 'w') as f:
                f.write(f"ACTIVADO|{datetime.now(timezone.utc).isoformat()}|{tipo_licencia}")
            
            flash(f'Sistema activado correctamente. Licencia: {tipo_licencia}', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Código de activación inválido', 'danger')
    
    # Obtener información de contacto
    email = Configuracion.query.filter_by(clave='email_contacto').first()
    telefono = Configuracion.query.filter_by(clave='telefono_contacto').first()
    qbapay = Configuracion.query.filter_by(clave='qbapay_link').first()
    btc = Configuracion.query.filter_by(clave='btc_address').first()
    usdt = Configuracion.query.filter_by(clave='usdt_address').first()
    
    # Obtener ID de máquina actual
    id_maquina = generar_id_maquina()
    
    return render_template('licencias/activacion.html',
                         id_maquina=id_maquina,
                         email=email.valor if email else 'megashopsc20@gmail.com',
                         telefono=telefono.valor if telefono else '+53 50625350',
                         qbapay_link=qbapay.valor if qbapay else '',
                         btc_address=btc.valor if btc else '',
                         usdt_address=usdt.valor if usdt else '')


@licencias_bp.route('/licencias')
@login_required
@admin_required
def gestionar_licencias():
    """Gestión de licencias (solo copia maestra)"""
    licencias = Licencia.query.order_by(Licencia.fecha_generacion.desc()).all()
    return render_template('licencias/gestionar.html', licencias=licencias)


@licencias_bp.route('/licencia/generar', methods=['GET', 'POST'])
@login_required
@admin_required
def generar_licencia():
    """Generar nueva licencia para cliente"""
    if request.method == 'POST':
        id_maquina = request.form.get('id_maquina', '').strip()
        cliente_nombre = request.form.get('cliente_nombre', '').strip()
        cliente_contacto = request.form.get('cliente_contacto', '').strip()
        tipo_licencia = request.form.get('tipo_licencia', 'estandar')
        notas = request.form.get('notas', '').strip()
        
        if not id_maquina:
            flash('El ID de máquina es requerido', 'warning')
            return render_template('licencias/generar.html')
        
        # Generar código
        codigo = generar_codigo_activacion(id_maquina, tipo_licencia)
        
        # Registrar en base de datos
        licencia = Licencia(
            id_maquina=id_maquina,
            codigo_activacion=codigo,
            cliente_nombre=cliente_nombre,
            cliente_contacto=cliente_contacto,
            tipo_licencia=tipo_licencia,
            notas=notas
        )
        db.session.add(licencia)
        db.session.commit()
        
        flash('Licencia generada correctamente', 'success')
        return render_template('licencias/generar.html', 
                             codigo_generado=codigo,
                             licencia=licencia)
    
    return render_template('licencias/generar.html', 
                         tipos_licencia=[
                             ('estandar', 'Estándar (1 taller, 1 PC) - 3500 CUP / 15 USD'),
                             ('ampliada', 'Ampliada (2 PCs mismo taller) - 6000 CUP / 25 USD'),
                             ('sucursales', 'Sucursales (hasta 5 instalaciones) - 12000 CUP / 50 USD')
                         ])


@licencias_bp.route('/licencia/<int:id>/revocar')
@login_required
@admin_required
def revocar_licencia(id):
    """Revocar licencia (control interno)"""
    licencia = db.session.get(Licencia, id)
    if not licencia:
        flash('Registro no encontrado', 'danger')
        return redirect(url_for('dashboard.index'))
    licencia.activa = False
    db.session.commit()
    flash('Licencia revocada', 'info')
    return redirect(url_for('licencias.gestionar_licencias'))


@licencias_bp.route('/api/id_maquina')
@login_required
def api_id_maquina():
    """API para obtener ID de máquina actual"""
    id_maquina = generar_id_maquina()
    return jsonify({'id_maquina': id_maquina})


@licencias_bp.route('/acerca_de')
@login_required
def acerca_de():
    """Página Acerca de"""
    version = "1.0.0"
    
    # Información de contacto
    email = Configuracion.query.filter_by(clave='email_contacto').first()
    telefono = Configuracion.query.filter_by(clave='telefono_contacto').first()
    qbapay = Configuracion.query.filter_by(clave='qbapay_link').first()
    btc = Configuracion.query.filter_by(clave='btc_address').first()
    usdt = Configuracion.query.filter_by(clave='usdt_address').first()
    
    # Estado de licencia
    license_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'license.dat')
    licencia_info = {'activada': False}
    
    if os.path.exists(license_file):
        with open(license_file, 'r') as f:
            datos = f.read().split('|')
            if len(datos) >= 3:
                licencia_info = {
                    'activada': True,
                    'tipo': datos[2],
                    'fecha': datos[1]
                }
    
    return render_template('licencias/acerca_de.html',
                         version=version,
                         licencia_info=licencia_info,
                         email=email.valor if email else 'megashopsc20@gmail.com',
                         telefono=telefono.valor if telefono else '+53 50625350',
                         qbapay_link=qbapay.valor if qbapay else '',
                         btc_address=btc.valor if btc else '',
                         usdt_address=usdt.valor if usdt else '')
