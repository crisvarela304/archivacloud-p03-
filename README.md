# ArchivaCloud - Pareja P-03

MVP de almacenamiento seguro de archivos de audio en AWS S3.

## Parametros (Anexo B)
| Campo | Valor |
|-------|-------|
| Bucket | archivacloud-p03 |
| Region | us-west-2 |
| Extensiones | MP3, WAV |
| Tamano max | 20 MB |
| Feature | Hash SHA-256 local |

## Stack
- Backend: Python / FastAPI / Boto3
- Frontend: React 18 / Vite 5 / Tailwind CSS

## Correr backend
```bash
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Correr frontend
```bash
cd frontend
npm install
npm run dev
```

## Variables de entorno
Copiar .env.example como ackend/.env y completar con credenciales AWS.
