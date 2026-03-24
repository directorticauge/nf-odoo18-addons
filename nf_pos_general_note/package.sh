#!/bin/bash

# Script para empaquetar el módulo nf_pos_general_note
# Uso: ./package.sh

MODULE_NAME="nf_pos_general_note"
VERSION="18.0.1.0"
OUTPUT_FILE="${MODULE_NAME}_v${VERSION}.zip"

echo "📦 Empaquetando módulo: $MODULE_NAME"
echo "📌 Versión: $VERSION"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "__manifest__.py" ]; then
    echo "❌ Error: Ejecutar este script desde el directorio del módulo"
    exit 1
fi

# Crear el archivo ZIP
cd ..
zip -r "$OUTPUT_FILE" "$MODULE_NAME" \
    -x "*.pyc" \
    -x "*/__pycache__/*" \
    -x "*/.DS_Store" \
    -x "*/package.sh" \
    -x "*/.git/*" \
    -x "*.swp"

if [ $? -eq 0 ]; then
    echo "✅ Módulo empaquetado exitosamente:"
    echo "📁 Archivo: $OUTPUT_FILE"
    echo "📏 Tamaño: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo ""
    echo "🚀 Listo para:"
    echo "   - Instalar en Odoo manualmente"
    echo "   - Subir a Odoo Apps Store"
    echo "   - Distribuir a clientes"
else
    echo "❌ Error al empaquetar el módulo"
    exit 1
fi
