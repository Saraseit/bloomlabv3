"""Migraciones de esquema versionadas.

El proyecto no usa una herramienta de migraciones, así que cada cambio de
esquema se registra aquí con un nombre único. Al arrancar la API se
ejecutan, en orden, las que todavía no aparecen en schema_migraciones.

Reglas:
- Nunca editar una migración ya publicada: agregar una nueva al final.
- Cada migración corre en su propia transacción; si falla, se revierte
  completa y la API no arranca, para no operar con un esquema a medias.
- Un advisory lock evita que dos instancias la apliquen a la vez.
"""

from app.database.connection import get_connection

# Número arbitrario y fijo para pg_advisory_xact_lock
_LOCK_MIGRACIONES = 874_201_553


MIGRACIONES = [
    (
        "2026_09_24_unidades_compra_uso",
        """
        -- ── Insumos: unidad de compra vs unidad de uso ──
        -- unidad            = unidad de compra (ya existía: "PAQ 24", "Costal"...)
        -- costo_referencia  = costo de UNA unidad de compra (ya existía)
        -- piezas_por_paquete: cuántas unidades de uso trae una unidad de compra
        -- unidad_uso        : cómo se captura en los arreglos ("tallo", "pieza")
        -- cobrar_paquete_completo: si en el evento se redondea hacia arriba
        --                   a paquetes completos (perecederos) o se cobra
        --                   solo la proporción (consumibles reutilizables)
        ALTER TABLE insumos
            ADD COLUMN IF NOT EXISTS unidad_uso VARCHAR(50);
        ALTER TABLE insumos
            ADD COLUMN IF NOT EXISTS piezas_por_paquete NUMERIC NOT NULL DEFAULT 1;
        ALTER TABLE insumos
            ADD COLUMN IF NOT EXISTS cobrar_paquete_completo BOOLEAN NOT NULL DEFAULT FALSE;

        ALTER TABLE insumos
            DROP CONSTRAINT IF EXISTS insumos_piezas_por_paquete_positivo;
        ALTER TABLE insumos
            ADD CONSTRAINT insumos_piezas_por_paquete_positivo
            CHECK (piezas_por_paquete > 0);

        -- ── Evento: costo de paquetes incompletos ──
        -- Va aparte, como el flete: no entra en la base de la comisión.
        ALTER TABLE eventos
            ADD COLUMN IF NOT EXISTS costo_sobrante NUMERIC NOT NULL DEFAULT 0;

        -- ── Foto congelada de los insumos de cada arreglo del evento ──
        -- Se toma al agregar el arreglo, igual que evento_arreglos.costo_unitario,
        -- para que editar el catálogo no cambie cotizaciones ya hechas.
        CREATE TABLE IF NOT EXISTS evento_arreglo_insumos (
            id                      SERIAL PRIMARY KEY,
            evento_arreglo_id       INTEGER NOT NULL
                REFERENCES evento_arreglos(id) ON DELETE CASCADE,
            insumo_id               INTEGER NOT NULL REFERENCES insumos(id),
            cantidad_uso            NUMERIC NOT NULL,
            costo_unitario_uso      NUMERIC NOT NULL,
            piezas_por_paquete      NUMERIC NOT NULL DEFAULT 1,
            costo_paquete           NUMERIC NOT NULL DEFAULT 0,
            porcentaje_merma        NUMERIC NOT NULL DEFAULT 0,
            cobrar_paquete_completo BOOLEAN NOT NULL DEFAULT FALSE,
            unidad_compra           VARCHAR(100),
            unidad_uso              VARCHAR(100)
        );

        CREATE INDEX IF NOT EXISTS idx_evento_arreglo_insumos_ea
            ON evento_arreglo_insumos (evento_arreglo_id);

        -- Foto de los arreglos que ya estaban en eventos. Todos los insumos
        -- existentes tienen factor 1 y sin redondeo, así que el costo de
        -- esos eventos no cambia.
        INSERT INTO evento_arreglo_insumos (
            evento_arreglo_id, insumo_id, cantidad_uso, costo_unitario_uso,
            piezas_por_paquete, costo_paquete, porcentaje_merma,
            cobrar_paquete_completo, unidad_compra, unidad_uso
        )
        SELECT
            ea.id, ad.insumo_id, ad.cantidad, ad.costo_real,
            i.piezas_por_paquete, i.costo_referencia, i.porcentaje_merma,
            i.cobrar_paquete_completo, i.unidad, COALESCE(i.unidad_uso, i.unidad)
        FROM evento_arreglos ea
        JOIN arreglo_detalle ad ON ad.arreglo_id = ea.arreglo_id
        JOIN insumos i          ON i.id = ad.insumo_id
        WHERE NOT EXISTS (
            SELECT 1 FROM evento_arreglo_insumos s
            WHERE s.evento_arreglo_id = ea.id
        );

        -- ── Gastos reales ligados a un insumo (planeado vs comprado) ──
        ALTER TABLE evento_gastos_reales
            ADD COLUMN IF NOT EXISTS insumo_id INTEGER REFERENCES insumos(id);
        ALTER TABLE evento_gastos_reales
            ADD COLUMN IF NOT EXISTS paquetes_comprados NUMERIC;
        """,
    ),
]


def aplicar_migraciones():
    """Aplica las migraciones pendientes. Se llama al arrancar la API."""

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migraciones (
                nombre      VARCHAR(200) PRIMARY KEY,
                aplicada_en TIMESTAMP NOT NULL DEFAULT now()
            )
        """)
        conn.commit()

        for nombre, sql in MIGRACIONES:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_MIGRACIONES,))

            cur.execute(
                "SELECT 1 FROM schema_migraciones WHERE nombre = %s",
                (nombre,)
            )
            if cur.fetchone():
                conn.commit()
                continue

            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migraciones (nombre) VALUES (%s)",
                (nombre,)
            )
            conn.commit()
            print(f"[migraciones] aplicada: {nombre}")

        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
