import { sleep } from 'k6'
import http from 'k6/http'
import { check } from 'k6'

// Configurable via environment variables
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080'
const UPLOAD_PATH = __ENV.UPLOAD_PATH || '/api/videos/upload'
const FILE_PATH = __ENV.FILE_PATH || 'MiJugadaPostman.mp4'
const TITLE = __ENV.TITLE || 'Tiro de tres puntos en movimiento'
// ACCESS_TOKEN must be provided via env var (no auth calls in this script)
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwZWRyby5sb3BlekBleGFtcGxlLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MCwicGVybWlzc2lvbnMiOltdLCJmaXJzdF9uYW1lIjoiUGVkcm8iLCJsYXN0X25hbWUiOiJMXHUwMGYzcGV6IiwiY2l0eSI6IkJvZ290XHUwMGUxIiwiZXhwIjoxNzYwOTY5NDM4LCJpYXQiOjE3NjA4ODMwMzgsInRva2VuX3R5cGUiOiJhY2Nlc3MifQ.c6peu5qUBGzW2xlwHOxx8ex8bWbNq1gbRHQ4jynLAPQ'

export const options = {
   // stages: [
   //     { duration: '10s', target: 5 },
       // { duration: '1m', target: 10 },
       // { duration: '10s', target: 0 },
    //],
    vus: 40,
    iterations: 40,
}

// Load file at init stage (open() is only available in init)
let FILE_BYTES = null
let FILE_NAME = null
try {
    // normalize possible leading slash in Windows absolute path like '/D:/...'
    let normalizedPath = FILE_PATH
    if (normalizedPath.match(/^\/[A-Za-z]:\//)) {
        normalizedPath = normalizedPath.replace(/^\//, '')
    }
    FILE_BYTES = open(normalizedPath, 'b')
    const size = FILE_BYTES && (FILE_BYTES.byteLength || FILE_BYTES.length || 0)
    FILE_NAME = normalizedPath.split(/[\\/]/).pop()
    console.log(`Loaded file '${normalizedPath}' (name='${FILE_NAME}', ${size} bytes) in init stage`)
} catch (err) {
    console.error(`Init: Cannot open file ${FILE_PATH}: ${err.message}`)
    FILE_BYTES = null
}


export default function () {
    if (!ACCESS_TOKEN) {
        throw new Error('ACCESS_TOKEN environment variable is required for this script')
    }
    const token = ACCESS_TOKEN
    console.log(`Using ACCESS_TOKEN from env (len=${token.length})`)

    if (!FILE_BYTES) {
        throw new Error(`No file bytes available for ${FILE_PATH}. Make sure the file exists and k6 can access it.`)
    }
    const fileContents = FILE_BYTES

    const filename = FILE_NAME || 'MiJugadaPostman.mp4'
    const form = {
        video_file: http.file(fileContents, filename, 'video/mp4'),
        title: TITLE,
    }

    const uploadUrl = `${BASE_URL}${UPLOAD_PATH}`

    console.info(`Upload URL: ${uploadUrl}`)

    const params = {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    }

    const res = http.post(uploadUrl, form, params)

    console.info(`Response status: ${res.status}`)
    console.info(`Response body: ${res.body}`)

    check(res, {
        'upload status ok': (r) => r.status === 200 || r.status === 201,
    })

}
