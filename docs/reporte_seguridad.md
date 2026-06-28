# Reporte de Seguridad (Controles SEC-01 a SEC-10)

En este proyecto se implementaron los siguientes controles de seguridad mínimos requeridos:

1. **SEC-01 (CORS Estricto):** En FastAPI (backend/main.py) se limitó allow_origins explícitamente a los puertos de desarrollo del frontend (http://localhost:5173 y http://127.0.0.1:5173), evitando ataques CSRF de orígenes desconocidos.
2. **SEC-02 (Separación de Credenciales):** Las credenciales de AWS no están hardcodeadas en el código (fuera del archivo temporal del script original que ya fue removido) y se cargan dinámicamente mediante el módulo python-dotenv y Pydantic BaseSettings (.env).
3. **SEC-03 (Expiración de Presigned URLs):** Las URLs firmadas que entrega el backend hacia el frontend tienen una vida útil máxima de 3600 segundos (1 hora), limitando la ventana de exposición.
4. **SEC-04 (Validación de Tipos MIME):** Se valida el campo content_type tanto en el frontend como en el backend, permitiendo solo 'audio/mpeg' y variaciones de 'audio/wav'.
5. **SEC-05 (Validación de Extensiones):** Se implementó una verificación estricta usando Pydantic en FastAPI que levanta HTTPException si la extensión del archivo no corresponde a .mp3 o .wav.
6. **SEC-06 (Límite de Tamaño de Subida):** El servidor (y el frontend) rechazan archivos que superen el límite de 20 MB, protegiendo al sistema de abusos o ataques DoS por agotamiento de almacenamiento.
7. **SEC-07 (Bloqueo de Acceso Público S3):** El bucket (archivacloud-p03) se configuró con 'Block all public access'.
8. **SEC-08 (Manejo de Errores Limpio):** Las excepciones HTTP y los mensajes de error devueltos por el backend no revelan stack traces internos ni datos de la infraestructura.
9. **SEC-09 (Integridad de Archivos - Feature Extra):** Se implementó el cálculo del hash SHA-256 en el navegador localmente antes de la subida, garantizando que el archivo no fue manipulado durante el tránsito.
10. **SEC-10 (Protección de Dependencias):** Se ejecutaron herramientas de auditoría tanto en backend (pip-audit) como en frontend (npm audit) mitigando vulnerabilidades conocidas en paquetes de terceros.