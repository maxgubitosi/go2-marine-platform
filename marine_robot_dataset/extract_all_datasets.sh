#!/bin/bash
# =============================================================
# Extrae datasets para TODOS los rosbags encontrados en ../rosbags/
# Ejecuta extract_dataset.py una vez por cada rosbag.
# Si el dataset ya existe (carpeta en datasets/), lo salta.
#
# Uso:  ./extract_all_datasets.sh
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROSBAGS_DIR="$SCRIPT_DIR/../rosbags"
DATASETS_DIR="$SCRIPT_DIR/datasets"

# Verificar que existe la carpeta de rosbags
if [ ! -d "$ROSBAGS_DIR" ]; then
    echo "ERROR: No se encontró la carpeta de rosbags: $ROSBAGS_DIR"
    exit 1
fi

# Contar rosbags (solo directorios que empiecen con marine_sim_)
bags=()
for bag in "$ROSBAGS_DIR"/marine_sim_*/; do
    [ -d "$bag" ] && bags+=("$bag")
done

total=${#bags[@]}
if [ "$total" -eq 0 ]; then
    echo "No se encontraron rosbags en $ROSBAGS_DIR"
    exit 1
fi

echo "=============================================="
echo " Extracción de datasets en lote"
echo " Rosbags encontrados: $total"
echo "=============================================="
echo ""

processed=0
skipped=0
failed=0

for bag_path in "${bags[@]}"; do
    bag_name=$(basename "$bag_path")
    dataset_path="$DATASETS_DIR/$bag_name"

    echo "----------------------------------------------"
    echo "[$((processed + skipped + failed + 1))/$total] $bag_name"
    echo "----------------------------------------------"

    # Saltar si ya existe el dataset con su CSV
    if [ -f "$dataset_path/dataset.csv" ]; then
        echo "  ⏭  Ya existe dataset, saltando."
        skipped=$((skipped + 1))
        continue
    fi

    echo "  🔄 Extrayendo dataset..."
    if python3 "$SCRIPT_DIR/extract_dataset.py" "$bag_path"; then
        echo "  ✅ Completado."
        processed=$((processed + 1))
    else
        echo "  ❌ Error al procesar $bag_name"
        failed=$((failed + 1))
    fi
    echo ""
done

echo "=============================================="
echo " Resumen"
echo "  Procesados:  $processed"
echo "  Saltados:    $skipped"
echo "  Fallidos:    $failed"
echo "  Total:       $total"
echo "=============================================="
