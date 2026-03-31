$salida = "MACMETRIC_CONTEXTO.txt"

# Limpiar archivo
"" | Out-File $salida

# =============================
# ESTADO (lo puedes editar después)
# =============================
"===== ESTADO ACTUAL DEL PROYECTO =====" | Out-File $salida -Append
"- (Actualiza manualmente este bloque si quieres)" | Out-File $salida -Append
"" | Out-File $salida -Append

# =============================
# ESTRUCTURA COMPLETA
# =============================
"===== ESTRUCTURA DEL PROYECTO (tree /F) =====" | Out-File $salida -Append
tree /F | Out-File $salida -Append
"" | Out-File $salida -Append

# =============================
# FUNCIÓN PARA AGREGAR ARCHIVOS
# =============================
function Agregar-Archivo($ruta) {
    if (Test-Path $ruta) {
        "===== $ruta =====" | Out-File $salida -Append
        Get-Content $ruta | Out-File $salida -Append
        "" | Out-File $salida -Append
    }
}

# =============================
# ARCHIVOS IMPORTANTES
# =============================
Agregar-Archivo "app\main.py"
Agregar-Archivo "app\core\database.py"
Agregar-Archivo "app\core\config.py"

Agregar-Archivo "app\web\routes\auth.py"
Agregar-Archivo "app\web\routes\users.py"
Agregar-Archivo "app\web\routes\dashboard.py"
Agregar-Archivo "app\web\routes\upload.py"

Agregar-Archivo "app\templates\login.html"
Agregar-Archivo "app\templates\users.html"
Agregar-Archivo "app\templates\base.html"

Agregar-Archivo "app\static\css\styles.css"

# =============================
# BACKEND (PROCESAMIENTO)
# =============================
Agregar-Archivo "backend\services\file_classifier.py"
Agregar-Archivo "backend\services\time_cleaner.py"
Agregar-Archivo "backend\services\time_metrics.py"

Agregar-Archivo "backend\utils\exporter.py"

Agregar-Archivo "backend\import_siirfe.py"

# =============================
# TESTS (OPCIONAL)
# =============================
Agregar-Archivo "backend\test_parser.py"
Agregar-Archivo "backend\test_metrics.py"

# =============================
# FIN
# =============================
"===== FIN DEL CONTEXTO =====" | Out-File $salida -Append

Write-Host "Contexto generado en $salida"