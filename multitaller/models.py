"""
Modelos de base de datos para MultiTaller
Sistema Integral de Gestión para Taller de Reparación de Equipos Informáticos
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Usuario(db.Model):
    """Tabla de usuarios con roles"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, tecnico, recepcionista
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nombre_completo': self.nombre_completo,
            'rol': self.rol,
            'activo': self.activo
        }


class Cliente(db.Model):
    """Tabla de clientes del taller"""
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono_fijo = db.Column(db.String(20))
    telefono_movil = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    tipo_cliente = db.Column(db.String(30))  # Persona natural, Mipyme, Empresa estatal, CPA, CNA, PDL
    identificacion = db.Column(db.String(50))  # Opcional
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    dispositivos = db.relationship('Dispositivo', backref='cliente', lazy=True)
    ordenes = db.relationship('Orden', backref='cliente', lazy=True)
    contratos = db.relationship('Contrato', backref='cliente', lazy=True)
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'telefono': self.telefono_movil or self.telefono_fijo,
            'tipo_cliente': self.tipo_cliente,
            'activo': self.activo
        }


class ModeloEquipo(db.Model):
    """Catálogo de marcas y modelos de equipos"""
    __tablename__ = 'modelos_equipo'
    
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # PC escritorio, Laptop, Impresora, etc.
    especificaciones = db.Column(db.Text)  # JSON o texto estructurado
    problemas_frecuentes = db.Column(db.Text)
    notas_servicio = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    dispositivos = db.relationship('Dispositivo', backref='modelo', lazy=True)
    piezas_compatibles = db.relationship('PiezaCompatible', backref='modelo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'marca': self.marca,
            'modelo': self.modelo,
            'tipo': self.tipo,
            'nombre_completo': f"{self.marca} {self.modelo}"
        }


class Dispositivo(db.Model):
    """Equipos de los clientes"""
    __tablename__ = 'dispositivos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    modelo_id = db.Column(db.Integer, db.ForeignKey('modelos_equipo.id'))
    marca = db.Column(db.String(100))
    modelo_texto = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    tipo = db.Column(db.String(50))  # Heredado del modelo o manual
    especificaciones_extra = db.Column(db.Text)
    foto_path = db.Column(db.String(255))  # Ruta a archivo local
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    ordenes = db.relationship('OrdenDispositivo', backref='dispositivo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente': self.cliente.nombre_completo if self.cliente else '',
            'marca': self.marca,
            'modelo': self.modelo_texto,
            'numero_serie': self.numero_serie,
            'tipo': self.tipo
        }


class Tecnico(db.Model):
    """Técnicos del taller"""
    __tablename__ = 'tecnicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    costo_hora = db.Column(db.Float, default=0)
    activo = db.Column(db.Boolean, default=True)
    
    ordenes_asignadas = db.relationship('Orden', backref='tecnico', lazy=True)


class Orden(db.Model):
    """Órdenes de servicio"""
    __tablename__ = 'ordenes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(20), unique=True, nullable=False)  # OT-AA-0001
    fecha_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega_prevista = db.Column(db.DateTime)
    fecha_entrega_real = db.Column(db.DateTime)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo_servicio = db.Column(db.String(50))  # Reparación, Mantenimiento, etc.
    estado_general = db.Column(db.String(30), default='Recibido')
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'))
    mano_obra_costo = db.Column(db.Float, default=0)
    costo_total = db.Column(db.Float, default=0)
    notas_internas = db.Column(db.Text)
    notas_cliente = db.Column(db.Text)
    garantia_meses = db.Column(db.Integer, default=0)
    fecha_fin_garantia = db.Column(db.DateTime)
    es_reingreso = db.Column(db.Boolean, default=False)
    orden_original_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'))
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    dispositivos_relacion = db.relationship('OrdenDispositivo', backref='orden', lazy=True)
    historial_estados = db.relationship('OrdenHistorialEstado', backref='orden', lazy=True)
    notas = db.relationship('OrdenNota', backref='orden', lazy=True)
    orden_hija = db.relationship('Orden', remote_side=[id], backref='orden_padre')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_orden': self.numero_orden,
            'cliente': self.cliente.nombre_completo if self.cliente else '',
            'tipo_servicio': self.tipo_servicio,
            'estado': self.estado_general,
            'fecha_entrada': self.fecha_entrada.strftime('%Y-%m-%d') if self.fecha_entrada else '',
            'tecnico': self.tecnico.nombre if self.tecnico else ''
        }


class OrdenDispositivo(db.Model):
    """Relación muchos a muchos entre órdenes y dispositivos"""
    __tablename__ = 'orden_dispositivos'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivos.id'), nullable=False)
    problema_reportado = db.Column(db.Text)
    diagnostico_tecnico = db.Column(db.Text)
    estado_individual = db.Column(db.String(30), default='Recibido')
    fecha_inicio_reparacion = db.Column(db.DateTime)
    fecha_fin_reparacion = db.Column(db.DateTime)
    notas_particulares = db.Column(db.Text)
    
    piezas_usadas = db.relationship('OrdenPieza', backref='orden_dispositivo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'dispositivo': self.dispositivo.marca + ' ' + (self.dispositivo.modelo_texto or '') if self.dispositivo else '',
            'problema': self.problema_reportado,
            'diagnostico': self.diagnostico_tecnico,
            'estado': self.estado_individual
        }


class OrdenPieza(db.Model):
    """Piezas utilizadas en una orden"""
    __tablename__ = 'orden_piezas'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_dispositivo_id = db.Column(db.Integer, db.ForeignKey('orden_dispositivos.id'), nullable=False)
    pieza_id = db.Column(db.Integer, db.ForeignKey('piezas.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    descuento_aplicado = db.Column(db.Float, default=0)
    fecha_uso = db.Column(db.DateTime, default=datetime.utcnow)
    es_garantia = db.Column(db.Boolean, default=False)  # No descuenta inventario
    
    pieza = db.relationship('Pieza', backref='usos_en_ordenes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'pieza': self.pieza.nombre if self.pieza else '',
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'total': self.cantidad * self.precio_unitario * (1 - self.descuento_aplicado / 100)
        }


class OrdenHistorialEstado(db.Model):
    """Historial de cambios de estado de órdenes"""
    __tablename__ = 'orden_historial_estados'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    estado_anterior = db.Column(db.String(30))
    estado_nuevo = db.Column(db.String(30), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref='historial_estados')


class OrdenNota(db.Model):
    """Notas internas de órdenes"""
    __tablename__ = 'orden_notas'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='notas')


class Proveedor(db.Model):
    """Proveedores de piezas"""
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    tipo = db.Column(db.String(30))  # formal, informal
    activo = db.Column(db.Boolean, default=True)
    
    piezas = db.relationship('Pieza', backref='proveedor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'contacto': self.contacto,
            'telefono': self.telefono,
            'tipo': self.tipo
        }


class Pieza(db.Model):
    """Inventario de piezas"""
    __tablename__ = 'piezas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50))  # Cartucho, Tóner, Placa, etc.
    codigo_interno = db.Column(db.String(50))
    cantidad = db.Column(db.Integer, default=0)
    cantidad_minima = db.Column(db.Integer, default=5)
    unidad = db.Column(db.String(20), default='unidad')
    precio_costo = db.Column(db.Float, default=0)
    precio_venta = db.Column(db.Float, default=0)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    descripcion = db.Column(db.Text)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    compatibles = db.relationship('PiezaCompatible', backref='pieza', lazy=True)
    movimientos = db.relationship('MovimientoInventario', backref='pieza', lazy=True)
    
    @property
    def bajo_stock(self):
        return self.cantidad <= self.cantidad_minima
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'codigo': self.codigo_interno,
            'cantidad': self.cantidad,
            'precio_costo': self.precio_costo,
            'precio_venta': self.precio_venta,
            'bajo_stock': self.bajo_stock
        }


class PiezaCompatible(db.Model):
    """Compatibilidad entre piezas y modelos de equipos"""
    __tablename__ = 'piezas_compatibles'
    
    id = db.Column(db.Integer, primary_key=True)
    pieza_id = db.Column(db.Integer, db.ForeignKey('piezas.id'), nullable=False)
    modelo_id = db.Column(db.Integer, db.ForeignKey('modelos_equipo.id'), nullable=False)
    notas_compatibilidad = db.Column(db.Text)


class MovimientoInventario(db.Model):
    """Movimientos de entrada y salida de inventario"""
    __tablename__ = 'movimientos_inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    pieza_id = db.Column(db.Integer, db.ForeignKey('piezas.id'), nullable=False)
    tipo_movimiento = db.Column(db.String(10), nullable=False)  # entrada, salida
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_movimiento = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    proveedor = db.relationship('Proveedor', backref='movimientos')
    usuario = db.relationship('Usuario', backref='movimientos')


class Contrato(db.Model):
    """Contratos de mantenimiento periódico"""
    __tablename__ = 'contratos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    frecuencia = db.Column(db.String(20))  # semanal, quincenal, mensual, etc.
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime)
    precio = db.Column(db.Float, default=0)
    cantidad_equipos = db.Column(db.Integer, default=1)
    activo = db.Column(db.Boolean, default=True)
    fecha_ultimo_servicio = db.Column(db.DateTime)
    
    ordenes = db.relationship('Orden', backref='contrato', lazy=True)
    
    def get_proximo_mantenimiento(self):
        """Calcula la fecha del próximo mantenimiento basado en la frecuencia"""
        if not self.fecha_ultimo_servicio:
            return self.fecha_inicio
        
        from datetime import timedelta
        dias = {
            'semanal': 7,
            'quincenal': 15,
            'mensual': 30,
            'trimestral': 90,
            'semestral': 180,
            'anual': 365
        }
        return self.fecha_ultimo_servicio + timedelta(days=dias.get(self.frecuencia, 30))


class CategoriaGasto(db.Model):
    """Categorías de gastos operativos"""
    __tablename__ = 'categorias_gastos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    
    gastos = db.relationship('Gasto', backref='categoria', lazy=True)


class Gasto(db.Model):
    """Gastos operativos del taller"""
    __tablename__ = 'gastos'
    
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_gastos.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    usuario = db.relationship('Usuario', backref='gastos')


class Configuracion(db.Model):
    """Configuración del sistema (clave-valor)"""
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogoTaller(db.Model):
    """Logo del taller para documentos"""
    __tablename__ = 'logo_taller'
    
    id = db.Column(db.Integer, primary_key=True)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    archivo_ruta = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)


class Licencia(db.Model):
    """Registro de licencias generadas (solo en copia maestra)"""
    __tablename__ = 'licencias'
    
    id = db.Column(db.Integer, primary_key=True)
    id_maquina = db.Column(db.String(100), nullable=False)
    codigo_activacion = db.Column(db.String(255), nullable=False)
    cliente_nombre = db.Column(db.String(100))
    cliente_contacto = db.Column(db.String(200))
    tipo_licencia = db.Column(db.String(50))  # estandar, ampliada, sucursales
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)
    notas = db.Column(db.Text)


class Notificacion(db.Model):
    """Sistema de notificaciones del taller"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='info')  # info, success, warning, danger
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    enlace = db.Column(db.String(255))  # URL opcional para redireccionar
    
    usuario = db.relationship('Usuario', backref='notificaciones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'tipo': self.tipo,
            'leida': self.leida,
            'fecha_creacion': self.fecha_creacion.strftime('%Y-%m-%d %H:%M') if self.fecha_creacion else '',
            'enlace': self.enlace
        }
