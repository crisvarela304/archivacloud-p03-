import { useState, useRef, useCallback, useEffect } from 'react'
import axios from 'axios'

const MAX_SIZE = 20 * 1024 * 1024
const ALLOWED  = ['.mp3', '.wav']

async function sha256(file) {
  const buf = await file.arrayBuffer()
  const h   = await crypto.subtle.digest('SHA-256', buf)
  return Array.from(new Uint8Array(h)).map(b => b.toString(16).padStart(2, '0')).join('')
}

function uploadS3(url, file, hash, onProgress) {
  return new Promise((res, rej) => {
    const xhr = new XMLHttpRequest()
    xhr.upload.onprogress = e => { if (e.lengthComputable) onProgress(Math.round(e.loaded / e.total * 100)) }
    xhr.onload  = () => xhr.status < 300 ? res(xhr.status) : rej(new Error('S3 error: ' + xhr.status))
    xhr.onerror = () => rej(new Error('Error de red'))
    xhr.open('PUT', url, true)
    xhr.setRequestHeader('Content-Type', file.type)
    if (hash) xhr.setRequestHeader('x-amz-meta-sha256', hash)
    xhr.send(file)
  })
}

function fmtSize(b) {
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1024 / 1024).toFixed(2) + ' MB'
}
function fmtDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('es-CL', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const [files,    setFiles]    = useState([])
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')
  const [hash,     setHash]     = useState('')
  const [status,   setStatus]   = useState('idle')
  const [progress, setProgress] = useState(0)
  const [dragging, setDragging] = useState(false)
  const ref = useRef(null)

  const fetchFiles = useCallback(async () => {
    setLoading(true)
    try { const { data } = await axios.get('/api/files'); setFiles(data) }
    catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchFiles() }, [fetchFiles])

  const handle = useCallback(async (file) => {
    setError(''); setHash(''); setProgress(0); setStatus('idle')
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED.includes(ext)) { setError('Solo MP3 y WAV'); return }
    if (file.size > MAX_SIZE)    { setError('Maximo 20 MB'); return }
    setStatus('hashing')
    const h = await sha256(file)
    setHash(h)
    setStatus('uploading')
    const ct = file.type || (file.name.endsWith('.mp3') ? 'audio/mpeg' : 'audio/wav')
    try {
      const { data } = await axios.post('/api/upload/presigned-url', {
        filename: file.name, content_type: ct, file_size: file.size, sha256: h
      })
      await uploadS3(data.url, file, h, setProgress)
      setStatus('done')
      setTimeout(fetchFiles, 1200)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setStatus('error')
    }
  }, [fetchFiles])

  const onDrop = e => {
    e.preventDefault(); setDragging(false)
    if (e.dataTransfer.files?.[0]) handle(e.dataTransfer.files[0])
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">ArchivaCloud</h1>
      <p className="text-gray-500 text-sm mb-8">Pareja P-03 · archivacloud-p03 · us-west-2</p>

      <div
        className={"border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-6 " +
          (dragging ? "border-indigo-400 bg-indigo-950/20" : "border-gray-700 hover:border-indigo-500")}
        onDrop={onDrop}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onClick={() => ref.current?.click()}
      >
        <input ref={ref} type="file" accept=".mp3,.wav" className="hidden"
          onChange={e => { if (e.target.files?.[0]) handle(e.target.files[0]); e.target.value = '' }} />
        <p className="font-medium">{dragging ? 'Suelta aqui' : 'Arrastra un archivo MP3 o WAV aqui'}</p>
        <p className="text-gray-500 text-sm mt-1">maximo 20 MB</p>
      </div>

