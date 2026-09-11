from app.database.connection import get_connection
from app.core.security import hash_password, verify_password


def obtener_usuarios(empresa_id: int):

    conn = get_connection()
    cur = conn.cursor()

    # password_hash nunca se selecciona: no debe salir de la base
    cur.execute("""
        SELECT
            id,
            empresa_id,
            nombre,
            email,
            rol,
            activo,
            ultimo_acceso,
            creado_en
        FROM usuarios
        WHERE empresa_id = %s
        ORDER BY creado_en
    """, (empresa_id,))

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    cur.close()
    conn.close()

    return resultado


def crear_usuario(data, empresa_id: int):

    conn = get_connection()
    cur = conn.cursor()

    email = data.email.lower().strip()

    cur.execute("""
        SELECT COUNT(*)
        FROM usuarios
        WHERE email = %s
    """, (email,))

    if cur.fetchone()[0]:

        cur.close()
        conn.close()

        return {
            "error": "El email ya está registrado"
        }

    cur.execute("""
        INSERT INTO usuarios (
            empresa_id,
            nombre,
            email,
            password_hash,
            rol,
            activo
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            TRUE
        )
        RETURNING id
    """, (
        empresa_id,
        data.nombre,
        email,
        hash_password(data.password),
        data.rol
    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Usuario creado",
        "id": nuevo_id
    }


def actualizar_usuario(usuario_id: int, data):

    conn = get_connection()
    cur = conn.cursor()

    email = data.email.lower().strip()

    cur.execute("""
        SELECT id
        FROM usuarios
        WHERE email = %s
          AND id != %s
    """, (email, usuario_id))

    if cur.fetchone():

        cur.close()
        conn.close()

        return {
            "error": "El email ya está en uso"
        }

    cur.execute("""
        UPDATE usuarios
        SET
            nombre = %s,
            email = %s,
            rol = %s,
            activo = %s
        WHERE id = %s
        RETURNING id
    """, (
        data.nombre,
        email,
        data.rol,
        data.activo,
        usuario_id
    ))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Usuario no encontrado"
        }

    return {
        "mensaje": "Usuario actualizado",
        "id": resultado[0]
    }


def cambiar_password(usuario_id: int, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT password_hash
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Usuario no encontrado"
        }

    # passlib lanza si el hash guardado no es legible (por ejemplo, uno
    # escrito por otra versión de bcrypt). Sin este try, ese caso subiría
    # como 500; así cualquier problema de hash termina en un 400 claro.
    try:
        valida = verify_password(data.password_actual, fila[0])
    except Exception:
        valida = False

    if not valida:

        cur.close()
        conn.close()

        return {
            "error": "La contraseña actual no es correcta"
        }

    cur.execute("""
        UPDATE usuarios
        SET password_hash = %s
        WHERE id = %s
    """, (
        hash_password(data.password_nuevo),
        usuario_id
    ))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Contraseña actualizada"
    }


def eliminar_usuario(usuario_id: int, admin_id: int):

    if usuario_id == admin_id:
        return {
            "error": "No puedes eliminarte"
        }

    conn = get_connection()
    cur = conn.cursor()

    # Borrado lógico, igual que el resto del sistema
    cur.execute("""
        UPDATE usuarios
        SET activo = FALSE
        WHERE id = %s
        RETURNING id
    """, (usuario_id,))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Usuario no encontrado"
        }

    return {
        "mensaje": "Usuario desactivado",
        "id": resultado[0]
    }
