import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'clave_secreta_adventista_7mo_dia'

def get_db():
    conn = sqlite3.connect('colegio.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with open('schema.sql', mode='r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()

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
        
        conn = get_db()
        user = conn.execute('SELECT * FROM usuarios WHERE usuario = ? AND password = ?', 
                            (user_input, pass_input)).fetchone()
        conn.close()
        
        if user:
            session['usuario'] = user['usuario']
            session['nombre'] = user['nombre_completo']
            session['rol'] = user['rol']
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
        
    conn = get_db()
    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        usr = request.form['usuario']
        pwd = request.form['password']
        rol = request.form['rol']
        conn.execute('INSERT INTO usuarios (nombre_completo, usuario, password, rol) VALUES (?, ?, ?, ?)',
                     (nombre, usr, pwd, rol))
        conn.commit()
        
    lista_usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
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
        
        conn = get_db()
        conn.execute('''UPDATE usuarios 
                        SET nombre_completo = ?, usuario = ?, password = ?, rol = ? 
                        WHERE id = ?''', (nombre, usr, pwd, rol, id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('usuarios'))

@app.route('/usuarios/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_usuario(id):
    if 'usuario' not in session or session.get('rol') != 'ADMIN':
        return redirect(url_for('seguimiento'))
        
    conn = get_db()
    # Permitir eliminar siempre que no sea la única cuenta activa o ID 1
    if id != 1:
        conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    
    return redirect(url_for('usuarios'))

# ==================== GESTIÓN DE ESTUDIANTES ====================

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    if request.method == 'POST':
        paterno = request.form['paterno']
        materno = request.form['materno']
        nombres = request.form['nombres']
        nivel = request.form['nivel']
        curso = request.form['curso']
        padre = request.form['nombre_padre']
        celular = request.form['celular_padre']
        domicilio = request.form['domicilio']
        
        conn.execute('''INSERT INTO estudiantes 
                     (paterno, materno, nombres, nivel, curso, nombre_padre, celular_padre, domicilio)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (paterno, materno, nombres, nivel, curso, padre, celular, domicilio))
        conn.commit()
        
    lista_estudiantes = conn.execute('SELECT * FROM estudiantes ORDER BY paterno, materno, nombres ASC').fetchall()
    conn.close()
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
        
        conn = get_db()
        conn.execute('''UPDATE estudiantes 
                        SET paterno = ?, materno = ?, nombres = ?, nivel = ?, curso = ?, 
                            nombre_padre = ?, celular_padre = ?, domicilio = ? 
                        WHERE id = ?''',
                     (paterno, materno, nombres, nivel, curso, padre, celular, domicilio, id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('estudiantes'))

@app.route('/estudiantes/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_estudiante(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    conn.execute('DELETE FROM seguimiento WHERE estudiante_id = ?', (id,))
    conn.execute('DELETE FROM estudiantes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('estudiantes'))

# ==================== SEGUIMIENTO Y REPORTES ====================

@app.route('/seguimiento')
def seguimiento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    nivel = request.args.get('nivel', 'Primaria')
    curso = request.args.get('curso', 1)
    
    conn = get_db()
    estudiantes_filtrados = conn.execute(
        'SELECT * FROM estudiantes WHERE nivel = ? AND curso = ? ORDER BY paterno, materno, nombres ASC',
        (nivel, curso)
    ).fetchall()
    conn.close()
    
    return render_template('seguimiento.html', estudiantes=estudiantes_filtrados, nivel_actual=nivel, curso_actual=int(curso))

@app.route('/guardar-seguimiento', methods=['POST'])
def guardar_seguimiento():
    if 'usuario' not in session:
        return jsonify({'status': 'error'}), 401
        
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO seguimiento (estudiante_id, materia, tipo_registro) VALUES (?, ?, ?)',
                 (data['estudiante_id'], data['materia'], data['tipo']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/reporte')
def reporte():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    estudiante_id = request.args.get('estudiante_id')
    estudiante = None
    registros = []
    
    conn = get_db()
    todos_estudiantes = conn.execute('SELECT * FROM estudiantes ORDER BY paterno, materno, nombres ASC').fetchall()
    
    if estudiante_id:
        estudiante = conn.execute('SELECT * FROM estudiantes WHERE id = ?', (estudiante_id,)).fetchone()
        registros = conn.execute('''SELECT * FROM seguimiento 
                                   WHERE estudiante_id = ? ORDER BY fecha DESC''', (estudiante_id,)).fetchall()
    conn.close()
    
    return render_template('reporte.html', estudiantes=todos_estudiantes, estudiante=estudiante, registros=registros)

# ==================== EJECUCIÓN AL FINAL DEL ARCHIVO ====================

if __name__ == '__main__':
    app.run(debug=True)