import http from 'k6/http'
import { check } from 'k6'



// Configurable via environment variables
// Para AWS: usar ALB DNS name obtenido de terraform output alb_dns_name
// Ejemplo: k6 run K6/0unaPeticion.js -e BASE_URL=http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com
const BASE_URL = __ENV.BASE_URL || 'http://anb-public-alb-170093693.us-east-1.elb.amazonaws.com'
const UPLOAD_PATH = __ENV.UPLOAD_PATH || '/api/videos/upload'
const FILE_PATH = __ENV.FILE_PATH || 'MiJugadaPostman.mp4'
const TITLE = __ENV.TITLE || 'Tiro de tres puntos en movimiento'
// ACCESS_TOKEN must be provided via env var (no auth calls in this script)
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwZWRyby5sb3BlekBleGFtcGxlLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MCwicGVybWlzc2lvbnMiOltdLCJmaXJzdF9uYW1lIjoiUGVkcm8iLCJsYXN0X25hbWUiOiJMXHUwMGYzcGV6IiwiY2l0eSI6IkJvZ290XHUwMGUxIiwiZXhwIjoxNzYyNzIzNTA0LCJpYXQiOjE3NjI2ODc1MDQsInRva2VuX3R5cGUiOiJhY2Nlc3MifQ.InYhxSpb5eGwHq-yUz9gJ0dzyf4834z9Ek4yVOhAqLQ'


export const options = {
    stages: [
        { duration: '1s', target: 5 },
        { duration: '5m', target: 5 }
    ],
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
} catch (err) {
    console.error(`Init: Cannot open file ${FILE_PATH}: ${err.message}`)
    FILE_BYTES = null
}


export default function () {
    if (!ACCESS_TOKEN) {
        throw new Error('ACCESS_TOKEN environment variable is required for this script')
    }
    const token = ACCESS_TOKEN

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


    const params = {
        headers: {
            Authorization: `Bearer ${token}`,
        },
        // per-request timeout fallback (ms) for k6 versions without setRequestTimeout
        timeout: 600000,
    }

    const res = http.post(uploadUrl, form, params)


    check(res, {
        'upload status ok': (r) => r.status === 201,
    })

}
