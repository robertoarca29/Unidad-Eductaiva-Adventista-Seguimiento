import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración de variables de entorno y seguridad
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_por_defecto_desarrollo')

# La URL de la BD debe provenir estrictamente de una variable de entorno en producción
database_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/adventistadb')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELOS (ORM) ====================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)
    paterno = db.Column(db.String(50))
    materno = db.Column(db.String(50))
    nombres = db.Column(db.String(100), nullable=False)
    nivel = db.Column(db.String(50))
    curso = db.Column(db.Integer)
    nombre_padre = db.Column(db.String(150))
    celular_padre = db.Column(db.String(20))
    domicilio = db.Column(db.String(200))
    seguimientos = db.relationship('Seguimiento', backref='estudiante', cascade="all, delete-orphan", lazy=True)

class Seguimiento(db.Model):
    __tablename__ = 'seguimiento'
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    materia = db.Column(db.String(100))
    tipo_registro = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, server_default=db.func.now())

# ==================== INICIALIZACIÓN DE BASE DE DATOS ====================

def init_db():
    with app.app_context():
        db.create_all()
        # Verificar y crear el usuario administrador por defecto si no existe
        admin_user = Usuario.query.filter_by(usuario='admin').first()
        if not admin_user:
            admin_defecto = Usuario(
                nombre_completo='Administrador del Sistema',
                usuario='admin',
                password=generate_password_hash('admin123'),
                rol='ADMIN'
            )
            db.session.add(admin_defecto)
            db.session.commit()

init_db()

# ==================== AUTENTICACIÓN Y NAVEGACIÓN ====================

@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('seguimiento'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form['usuario']
        pass_input = request.form['password']
        
        user = Usuario.query.filter_by(usuario=user_input).first()
        
        if user and check_password_hash(user.password, pass_input):
            session['usuario'] = user.usuario
            session['nombre'] = user.nombre_completo
            session['rol'] = user.rol
            return redirect(url_for('seguimiento'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==================== GESTIÓN DE USUARIOS ====================

@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    if request.method == 'POST':
        nuevo_usuario = Usuario(
            nombre_completo=request.form['nombre_completo'],
            usuario=request.form['usuario'],
            password=generate_password_hash(request.form['password']),
            rol=request.form['rol']
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    user = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        user.nombre_completo = request.form['nombre_completo']
        user.usuario = request.form['usuario']
        user.rol = request.form['rol']
        
        # Solo actualizar la contraseña si se ingresó un nuevo valor
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
            
        db.session.commit()
        
    return redirect(url_for('usuarios'))

@app.route('/usuarios/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_usuario(id):
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    if id != 1:
        user = Usuario.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
    
    return redirect(url_for('usuarios'))

# ==================== GESTIÓN DE ESTUDIANTES ====================

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        nuevo_estudiante = Estudiante(
            paterno=request.form['paterno'],
            materno=request.form['materno'],
            nombres=request.form['nombres'],
            nivel=request.form['nivel'],
            curso=int(request.form['curso']),
            nombre_padre=request.form['nombre_padre'],
            celular_padre=request.form['celular_padre'],
            domicilio=request.form['domicilio']
        )
        db.session.add(nuevo_estudiante)
        db.session.commit()
        
    lista_estudiantes = Estudiante.query.order_by(Estudiante.paterno, Estudiante.materno, Estudiante.nombres).all()
    return render_template('estudiantes.html', estudiantes=lista_estudiantes)

@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
def editar_estudiante(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    estudiante = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        estudiante.paterno = request.form['paterno']
        estudiante.materno = request.form['materno']
        estudiante.nombres = request.form['nombres']
        estudiante.nivel = request.form['nivel']
        estudiante.curso = int(request.form['curso'])
        estudiante.nombre_padre = request.form['nombre_padre']
        estudiante.celular_padre = request.form['celular_padre']
        estudiante.domicilio = request.form['domicilio']
        
        db.session.commit()
        
    return redirect(url_for('estudiantes'))

@app.route('/estudiantes/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_estudiante(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    estudiante = Estudiante.query.get(id)
    if estudiante:
        db.session.delete(estudiante) # La relación cascade eliminará los registros de seguimiento asociados
        db.session.commit()
    
    return redirect(url_for('estudiantes'))

# ==================== SEGUIMIENTO Y REPORTES ====================

@app.route('/seguimiento')
def seguimiento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    nivel = request.args.get('nivel', 'Primaria')
    curso = int(request.args.get('curso', 1))
    
    estudiantes_filtrados = Estudiante.query.filter_by(
        nivel=nivel, curso=curso
    ).order_by(Estudiante.paterno, Estudiante.materno, Estudiante.nombres).all()
    
    return render_template('seguimiento.html', estudiantes=estudiantes_filtrados, nivel_actual=nivel, curso_actual=curso)

@app.route('/guardar-seguimiento', methods=['POST'])
def guardar_seguimiento():
    if 'usuario' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401
        
    data = request.json
    nuevo_registro = Seguimiento(
        estudiante_id=data['estudiante_id'],
        materia=data['materia'],
        tipo_registro=data['tipo']
    )
    db.session.add(nuevo_registro)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/reporte')
def reporte():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    estudiante_id = request.args.get('estudiante_id')
    estudiante = None
    registros = []
    
    todos_estudiantes = Estudiante.query.order_by(Estudiante.paterno, Estudiante.materno, Estudiante.nombres).all()
    
    if estudiante_id:
        estudiante = Estudiante.query.get(estudiante_id)
        if estudiante:
            registros = Seguimiento.query.filter_by(
                estudiante_id=estudiante_id
            ).order_by(Seguimiento.fecha.desc()).all()
    
    return render_template('reporte.html', estudiantes=todos_estudiantes, estudiante=estudiante, registros=registros)

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    app.run(debug=True)