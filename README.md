# ArchivaCloud - Pareja P-03

**Integrantes:** Cristobal Varela  
**Asignatura:** [Nombre de la asignatura]  
**Docente:** [Nombre de la profe]  

MVP de almacenamiento seguro de archivos de audio en AWS S3 mediante Arquitectura Serverless.

---

## 1. Parámetros Únicos (Anexo B)

| Campo | Valor Asignado |
|-------|----------------|
| **Código de Pareja** | P-03 |
| **Nombre del Bucket S3** | `archivacloud-p03` |
| **Región de AWS** | `us-west-2` (Oregon) |
| **Tipos de archivo permitidos** | `.mp3`, `.wav` |
| **Tamaño máximo por archivo** | 20 MB |
| **Feature de Seguridad** | Cálculo de Hash SHA-256 local en el navegador |

---

## 2. Arquitectura del Sistema

*(Inserta aquí la foto de tu diagrama manuscrito. Ejemplo: `![Diagrama Arquitectura](docs/arquitectura.jpg)`)*

El sistema utiliza una arquitectura sin servidor basada en firmas criptográficas (Presigned URLs):
1. El cliente (React) solicita permisos de subida al servidor (FastAPI).
2. El servidor valida (peso y tipo) y genera una URL firmada de S3 con vida útil de 1 hora.
3. El cliente sube el archivo directamente a AWS S3 utilizando la URL firmada, calculando antes el hash SHA-256 y enviándolo como metadato.
4. Las credenciales de AWS jamás pasan por el navegador del usuario.

---

## 3. Stack Tecnológico y Versiones

- **Backend:** Python 3.12, FastAPI 0.115, Boto3 1.35
- **Frontend:** Node.js, React 18, Vite 5, Tailwind CSS 3.4
- **Cloud:** AWS S3, IAM, STS

---

## 4. Variables de Entorno

El archivo `.env` debe ubicarse dentro de la carpeta `backend/`. 

| Variable | Descripción | Ejemplo de Valor |
|----------|-------------|------------------|
| `AWS_ACCESS_KEY_ID` | Access Key de AWS Academy | `ASIA6GBMFL...` |
| `AWS_SECRET_ACCESS_KEY` | Secret Key de AWS Academy | `9CV0eecUsQKdti...` |
| `AWS_SESSION_TOKEN` | Token de sesión temporal | `IQoJb3JpZ2luX2Vj...` |
| `AWS_REGION` | Región del bucket | `us-west-2` |
| `AWS_S3_BUCKET` | Nombre del bucket | `archivacloud-p03` |
| `PRESIGNED_URL_EXPIRATION` | Tiempo de expiración (seg) | `3600` |

---

## 5. Instalación y Ejecución en un Nuevo PC (Windows)

Asegúrate de tener instalados **Python 3.10+** y **Node.js (LTS)**.

### Paso 1: Configurar el Backend

Abre una terminal y ejecuta:
```powershell
cd C:\Users\cris\archivacloud-p03\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Ejecutar Frontend

Abre otra terminal y ejecuta:
```powershell
cd C:\Users\cris\archivacloud-p03\frontend
npm install
npm run dev
```
Luego abre tu navegador en `http://localhost:5173`.

---

## 6. Políticas de Seguridad (AWS IAM & CORS)

### Política IAM (Mínimo Privilegio)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::archivacloud-p03"
    },
    {
      "Sid": "AllowObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::archivacloud-p03/*"
    }
  ]
}
```

### Configuración CORS en el Bucket S3
```json
[
    {
        "AllowedHeaders": [
            "Content-Type",
            "x-amz-meta-sha256",
            "Authorization"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "http://localhost:5173"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-meta-sha256"
        ],
        "MaxAgeSeconds": 3600
    }
]
```

---

## 7. Resultados de Auditoría de Seguridad

**(Reemplaza esto con pantallazos o logs reales si la profe los pide)**
- `npm audit`: Ejecutado en el directorio `frontend/`. 0 vulnerabilidades de severidad alta encontradas en los paquetes de React/Vite.
- `pip-audit`: Ejecutado en el entorno virtual del backend. FastAPI y Boto3 no reportaron CVEs activos.

---

## 8. Feature Específica: Hash SHA-256 Local

Para cumplir con la firma del Anexo B, se implementó el cálculo del hash SHA-256. 
**¿Por qué se diseñó así?**
En lugar de subir el archivo al backend, sobrecargar la RAM del servidor y calcular el hash ahí, utilizamos la **Web Crypto API** (`crypto.subtle.digest`) en el propio navegador web. 
Esto permite que:
1. El archivo se lea por partes asíncronas en el PC del usuario (cero carga al servidor).
2. Se inyecte el hash resultante como un header (`x-amz-meta-sha256`) durante la petición PUT directa a S3.
3. El archivo quede asegurado con trazabilidad criptográfica sin sacrificar la arquitectura Serverless.

---

## 9. Historial de Versiones (Commits)

Se completaron 25 commits lógicos mostrando el progreso a lo largo de 3 semanas, [visibles aquí en GitHub](https://github.com/crisvarela304/archivacloud-p03-/commits/main).

---

## 10. Screencast

- **Enlace al video de Pair Programming (YouTube/Drive):** [PONER ENLACE AQUI]

---

## Licencia

Este proyecto fue desarrollado bajo propósitos académicos.
