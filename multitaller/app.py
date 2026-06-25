"""
Aplicación principal de MultiTaller
Sistema Integral de Gestión para Taller de Reparación de Equipos Informáticos
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Configuracion, Licencia

# Importar rutas
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.clientes import clientes_bp
from routes.modelos import modelos_bp
from routes.dispositivos import dispositivos_bp
from routes.ordenes import ordenes_bp
from routes.inventario import inventario_bp
from routes.proveedores import proveedores_bp
from routes.tecnicos import tecnicos_bp
from routes.contratos import contratos_bp
from routes.gastos import gastos_bp
from routes.reportes import reportes_bp
from routes.configuracion import configuracion_bp
from routes.licencias import licencias_bp
from routes.ayuda import ayuda_bp
from routes.notificaciones import notificaciones_bp as notificaciones_bp


def create_app():
    """Factory de aplicación Flask"""
    app = Flask(__name__)
    
    # SECRET_KEY desde variable de entorno o valor por defecto seguro
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///multitaller.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    
    # Seguridad de sesiones Flask
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    
    # Validación de subida de archivos
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(modelos_bp)
    app.register_blueprint(dispositivos_bp)
    app.register_blueprint(ordenes_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(proveedores_bp)
    app.register_blueprint(tecnicos_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(gastos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(licencias_bp)
    app.register_blueprint(ayuda_bp)
    app.register_blueprint(notificaciones_bp)
    
    @app.route('/')
    def index():
        """Página principal - redirige según estado de autenticación y licencia"""
        if 'usuario_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Verificar licencia
        if not verificar_licencia():
            return redirect(url_for('licencias.activacion'))
        
        return redirect(url_for('dashboard.index'))
    
    @app.context_processor
    def utility_processor():
        """Variables disponibles en todos los templates"""
        usuario = None
        menu_visible = False
        dias_prueba = 0
        
        if 'usuario_id' in session:
            usuario = db.session.get(Usuario, session['usuario_id'])
            menu_visible = True
        
        # Información de licencia
        info_licencia = obtener_info_licencia()
        
        return {
            'usuario': usuario,
            'menu_visible': menu_visible,
            'info_licencia': info_licencia,
            'year': datetime.now().year
        }
    
    def verificar_licencia():
        """Verifica si el sistema está activado o en período de prueba"""
        # En producción, esto verifica el archivo license.dat
        # Para desarrollo, permitimos acceso
        license_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'license.dat')
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                datos = f.read().split('|')
                if len(datos) >= 3 and datos[0] == 'ACTIVADO':
                    return True
        
        # Verificar período de prueba
        primera_ejecucion = Configuracion.query.filter_by(clave='primera_ejecucion').first()
        if not primera_ejecucion:
            # Primera ejecución - iniciar período de prueba
            now = datetime.now(timezone.utc)
            conf = Configuracion(clave='primera_ejecucion', valor=now.isoformat(), 
                               descripcion='Fecha de primera ejecución')
            db.session.add(conf)
            db.session.commit()
            return True
        
        # Calcular días restantes
        fecha_inicio = datetime.fromisoformat(primera_ejecucion.valor)
        dias_transcurridos = (datetime.now(timezone.utc) - fecha_inicio).days
        
        if dias_transcurridos <= 15:
            return True
        
        return False
    
    def obtener_info_licencia():
        """Obtiene información sobre el estado de la licencia"""
        license_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'license.dat')
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                datos = f.read().split('|')
                if len(datos) >= 3 and datos[0] == 'ACTIVADO':
                    return {
                        'activada': True,
                        'tipo': datos[2] if len(datos) > 2 else 'estandar',
                        'mensaje': 'Sistema activado'
                    }
        
        # Período de prueba
        primera_ejecucion = Configuracion.query.filter_by(clave='primera_ejecucion').first()
        if primera_ejecucion:
            fecha_inicio = datetime.fromisoformat(primera_ejecucion.valor)
            dias_transcurridos = (datetime.now(timezone.utc) - fecha_inicio).days
            dias_restantes = max(0, 15 - dias_transcurridos)
            
            return {
                'activada': False,
                'en_prueba': True,
                'dias_restantes': dias_restantes,
                'mensaje': f'Versión de evaluación - Días restantes: {dias_restantes}'
            }
        
        return {
            'activada': False,
            'en_prueba': True,
            'dias_restantes': 15,
            'mensaje': 'Período de prueba iniciado'
        }
    
    # Crear tablas y usuario admin por defecto
    with app.app_context():
        db.create_all()
        crear_usuario_admin()
        inicializar_configuracion()
    
    return app


def crear_usuario_admin():
    """Crea usuario administrador por defecto si no existe"""
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        # Verificar si la contraseña está en variables de entorno
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin = Usuario(
            username='admin',
            password_hash=generate_password_hash(admin_password),
            nombre_completo='Administrador',
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Usuario admin creado: admin / {admin_password}")


def inicializar_configuracion():
    """Inicializa configuración básica del sistema"""
    configs_defecto = {
        'moneda_principal': ('CUP', 'Moneda principal del taller'),
        'moneda_secundaria': ('MLC', 'Moneda secundaria para equivalencias'),
        'tasa_cambio': ('1.0', 'Tasa de cambio de moneda secundaria a principal'),
        'regimen_tributario': ('general', 'Régimen tributario: general o simplificado'),
        'isip_tramos': (json.dumps([
            {"hasta": 5000, "porcentaje": 5},
            {"hasta": 10000, "porcentaje": 10},
            {"hasta": 20000, "porcentaje": 15},
            {"hasta": 50000, "porcentaje": 20},
            {"hasta": None, "porcentaje": 25}
        ]), 'Tramos del ISIP (JSON)'),
        'seguridad_social_porcentaje': ('5', 'Porcentaje de Seguridad Social sobre ganancia'),
        'cuota_fija_mensual': ('500', 'Cuota fija mensual para régimen simplificado'),
        'nombre_taller': ('Mi Taller', 'Nombre del taller'),
        'direccion_taller': ('', 'Dirección del taller'),
        'telefono_taller': ('', 'Teléfono del taller'),
        'email_contacto': ('megashopsc20@gmail.com', 'Email de contacto para licencias'),
        'telefono_contacto': ('+53 50625350', 'Teléfono de contacto para licencias'),
        'qbapay_link': ('', 'Enlace de pago Qbapay'),
        'btc_address': ('', 'Dirección Bitcoin para pagos'),
        'usdt_address': ('', 'Dirección USDT TRC20 para pagos')
    }
    
    for clave, (valor, descripcion) in configs_defecto.items():
        existing = Configuracion.query.filter_by(clave=clave).first()
        if not existing:
            conf = Configuracion(clave=clave, valor=valor, descripcion=descripcion)
            db.session.add(conf)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error inicializando configuración: {e}")


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
