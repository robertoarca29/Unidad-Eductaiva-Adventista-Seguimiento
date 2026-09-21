import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_super_segura')

# Configuración de base de datos
database_url = os.environ.get('DATABASE_URL', 'sqlite:///tu_base.db')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== INICIALIZACIÓN DE TABLAS ====================

def init_db():
    with app.app_context():
        # Crear tablas si no existen
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre_completo VARCHAR(150),
                usuario VARCHAR(50) UNIQUE,
                password VARCHAR(255),
                rol VARCHAR(20)
            );
        '''))
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS estudiantes (
                id SERIAL PRIMARY KEY,
                paterno VARCHAR(50),
                materno VARCHAR(50),
                nombres VARCHAR(100),
                nivel VARCHAR(50),
                curso INT,
                nombre_padre VARCHAR(150),
                celular_padre VARCHAR(20),
                domicilio VARCHAR(200)
            );
        '''))
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS seguimiento (
                id SERIAL PRIMARY KEY,
                estudiante_id INT,
                materia VARCHAR(100),
                tipo_registro VARCHAR(50),
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        '''))
        db.session.commit()

        # Insertar o actualizar la contraseña cifrada del usuario 'admin'
        hashed_pw = generate_password_hash('admin123')
        usr_check = db.session.execute(
            text("SELECT id FROM usuarios WHERE usuario = 'admin'")
        ).fetchone()

        if not usr_check:
            db.session.execute(
                text("INSERT INTO usuarios (nombre_completo, usuario, password, rol) VALUES (:n, :u, :p, :r)"),
                {'n': 'Administrador del Sistema', 'u': 'admin', 'p': hashed_pw, 'r': 'ADMIN'}
            )
        else:
            db.session.execute(
                text("UPDATE usuarios SET password = :p WHERE usuario = 'admin'"),
                {'p': hashed_pw}
            )
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
        
        result = db.session.execute(
            text('SELECT * FROM usuarios WHERE usuario = :u'),
            {'u': user_input}
        ).mappings().fetchone()
        
        if result and check_password_hash(result['password'], pass_input):
            session['usuario'] = result['usuario']
            session['nombre'] = result['nombre_completo']
            session['rol'] = result['rol']
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
        nombre = request.form['nombre_completo']
        usr = request.form['usuario']
        pwd = generate_password_hash(request.form['password'])
        rol = request.form['rol']
        
        db.session.execute(
            text('INSERT INTO usuarios (nombre_completo, usuario, password, rol) VALUES (:n, :u, :p, :r)'),
            {'n': nombre, 'u': usr, 'p': pwd, 'r': rol}
        )
        db.session.commit()
        
    lista_usuarios = db.session.execute(text('SELECT * FROM usuarios')).mappings().fetchall()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        usr = request.form['usuario']
        pwd = request.form['password']
        rol = request.form['rol']
        
        if pwd:
            hashed_pwd = generate_password_hash(pwd)
            db.session.execute(
                text('''UPDATE usuarios 
                        SET nombre_completo = :n, usuario = :u, password = :p, rol = :r 
                        WHERE id = :id'''),
                {'n': nombre, 'u': usr, 'p': hashed_pwd, 'r': rol, 'id': id}
            )
        else:
            db.session.execute(
                text('''UPDATE usuarios 
                        SET nombre_completo = :n, usuario = :u, rol = :r 
                        WHERE id = :id'''),
                {'n': nombre, 'u': usr, 'r': rol, 'id': id}
            )
        db.session.commit()
        
    return redirect(url_for('usuarios'))

@app.route('/usuarios/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_usuario(id):
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    if id != 1:
        db.session.execute(text('DELETE FROM usuarios WHERE id = :id'), {'id': id})
        db.session.commit()
    
    return redirect(url_for('usuarios'))

# ==================== GESTIÓN DE ESTUDIANTES ====================

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        paterno = request.form['paterno']
        materno = request.form['materno']
        nombres = request.form['nombres']
        nivel = request.form['nivel']
        curso = request.form['curso']
        padre = request.form['nombre_padre']
        celular = request.form['celular_padre']
        domicilio = request.form['domicilio']
        
        db.session.execute(
            text('''INSERT INTO estudiantes 
                    (paterno, materno, nombres, nivel, curso, nombre_padre, celular_padre, domicilio)
                    VALUES (:pat, :mat, :nom, :niv, :cur, :pad, :cel, :dom)'''),
            {'pat': paterno, 'mat': materno, 'nom': nombres, 'niv': nivel, 'cur': curso, 'pad': padre, 'cel': celular, 'dom': domicilio}
        )
        db.session.commit()
        
    lista_estudiantes = db.session.execute(text('SELECT * FROM estudiantes ORDER BY paterno, materno, nombres ASC')).mappings().fetchall()
    return render_template('estudiantes.html', estudiantes=lista_estudiantes)

@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
def editar_estudiante(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        paterno = request.form['paterno']
        materno = request.form['materno']
        nombres = request.form['nombres']
        nivel = request.form['nivel']
        curso = request.form['curso']
        padre = request.form['nombre_padre']
        celular = request.form['celular_padre']
        domicilio = request.form['domicilio']
        
        db.session.execute(
            text('''UPDATE estudiantes 
                    SET paterno = :pat, materno = :mat, nombres = :nom, nivel = :niv, curso = :cur, 
                        nombre_padre = :pad, celular_padre = :cel, domicilio = :dom 
                    WHERE id = :id'''),
            {'pat': paterno, 'mat': materno, 'nom': nombres, 'niv': nivel, 'cur': curso, 'pad': padre, 'cel': celular, 'dom': domicilio, 'id': id}
        )
        db.session.commit()
        
    return redirect(url_for('estudiantes'))

@app.route('/estudiantes/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_estudiante(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    db.session.execute(text('DELETE FROM seguimiento WHERE estudiante_id = :id'), {'id': id})
    db.session.execute(text('DELETE FROM estudiantes WHERE id = :id'), {'id': id})
    db.session.commit()
    
    return redirect(url_for('estudiantes'))

# ==================== SEGUIMIENTO Y REPORTES ====================

@app.route('/seguimiento')
def seguimiento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    nivel = request.args.get('nivel', 'Primaria')
    curso = request.args.get('curso', 1)
    
    estudiantes_filtrados = db.session.execute(
        text('SELECT * FROM estudiantes WHERE nivel = :niv AND curso = :cur ORDER BY paterno, materno, nombres ASC'),
        {'niv': nivel, 'cur': curso}
    ).mappings().fetchall()
    
    return render_template('seguimiento.html', estudiantes=estudiantes_filtrados, nivel_actual=nivel, curso_actual=int(curso))

@app.route('/guardar-seguimiento', methods=['POST'])
def guardar_seguimiento():
    if 'usuario' not in session:
        return jsonify({'status': 'error'}), 401
        
    data = request.json
    db.session.execute(
        text('INSERT INTO seguimiento (estudiante_id, materia, tipo_registro) VALUES (:e_id, :mat, :tipo)'),
        {'e_id': data['estudiante_id'], 'mat': data['materia'], 'tipo': data['tipo']}
    )
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/reporte')
def reporte():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    estudiante_id = request.args.get('estudiante_id')
    estudiante = None
    registros = []
    
    todos_estudiantes = db.session.execute(text('SELECT * FROM estudiantes ORDER BY paterno, materno, nombres ASC')).mappings().fetchall()
    
    if estudiante_id:
        estudiante = db.session.execute(
            text('SELECT * FROM estudiantes WHERE id = :id'),
            {'id': estudiante_id}
        ).mappings().fetchone()
        
        registros = db.session.execute(
            text('SELECT * FROM seguimiento WHERE estudiante_id = :id ORDER BY fecha DESC'),
            {'id': estudiante_id}
        ).mappings().fetchall()
    
    return render_template('reporte.html', estudiantes=todos_estudiantes, estudiante=estudiante, registros=registros)

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    app.run(debug=True)