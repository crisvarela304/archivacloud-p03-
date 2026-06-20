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
