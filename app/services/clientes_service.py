from app.database.connection import get_connection


def obtener_clientes():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nombre,
            telefono,
            email,
            empresa,
            notas,
            comision_porcentaje,
            activo,
            fecha_creacion
        FROM clientes
        WHERE activo = TRUE
        ORDER BY nombre
    """)

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


def crear_cliente(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO clientes (

            nombre,
            telefono,
            email,
            empresa,
            notas,
            comision_porcentaje,
            activo
        )
                
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,    
            TRUE
        )
        RETURNING id
    """, (

        data.nombre,
        data.telefono,
        data.email,
        data.empresa,
        data.notas,
        data.comision_porcentaje

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente creado",
        "id": nuevo_id
    }

def actualizar_cliente(cliente_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE clientes
        SET
            nombre = %s,
            telefono = %s,
            email = %s,
            empresa = %s,
            notas = %s
            comision_porcentaje = %s
        WHERE id = %s
    """, (

        data.nombre,
        data.telefono,
        data.email,
        data.empresa,
        data.notas,
        data.comision_porcentaje,
        cliente_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente actualizado"
    }

def eliminar_cliente(cliente_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE clientes
        SET activo = FALSE
        WHERE id = %s
    """, (cliente_id,))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente eliminado"
    }

