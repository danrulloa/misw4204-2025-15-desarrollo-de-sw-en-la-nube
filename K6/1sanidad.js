import http from 'k6/http'
import { check } from 'k6'
import { Trend } from 'k6/metrics'



// Configurable via environment variables
const BASE_URL = __ENV.BASE_URL || 'http://anb-public-alb-343736265.us-east-1.elb.amazonaws.com:80'
const UPLOAD_PATH = __ENV.UPLOAD_PATH || '/api/videos/upload'
const FILE_PATH = __ENV.FILE_PATH || 'MiJugadaPostman.mp4'
const TITLE = __ENV.TITLE || 'Tiro de tres puntos en movimiento'
// ACCESS_TOKEN must be provided via env var (no auth calls in this script)
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LnVzZXIuMTc2MTUxMDg0ODA5NkBleGFtcGxlLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MCwicGVybWlzc2lvbnMiOltdLCJmaXJzdF9uYW1lIjoiVGVzdCIsImxhc3RfbmFtZSI6IlVzZXIiLCJjaXR5IjoiQm9nb3RcdTAwZTEiLCJleHAiOjE3NjE3Nzc1ODAsImlhdCI6MTc2MTc0MTU4MCwidG9rZW5fdHlwZSI6ImFjY2VzcyJ9.bnIjpMWSNLPYy7feVsJrwHuetKSTOv855Zrs98h1xz8'

export const options = {
    stages: [
        { duration: '1m', target: 5 }
    ],
    discardResponseBodies: true,
    summaryTrendStats: ['min', 'avg', 'med', 'p(90)', 'p(95)', 'p(99)'],
    thresholds: {
        http_req_duration: ['p(95)<5000'],
        http_req_sending: ['p(95)<3000'],
        http_req_waiting: ['p(95)<4000'],
    },
    //vus: 50,
    //iterations: 50,
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

// Métricas personalizadas por fase
const t_blocked = new Trend('timing_blocked')
const t_connecting = new Trend('timing_connecting')
const t_sending = new Trend('timing_sending')
const t_waiting = new Trend('timing_waiting')
const t_receiving = new Trend('timing_receiving')
const upload_rate_mb_s = new Trend('upload_rate_mb_s')


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

    // Registrar timings para identificar el cuello de botella
    t_blocked.add(res.timings.blocked)
    t_connecting.add(res.timings.connecting)
    t_sending.add(res.timings.sending)
    t_waiting.add(res.timings.waiting)
    t_receiving.add(res.timings.receiving)

    // Calcular tasa de subida efectiva (MB/s) durante la fase de envío
    const sizeBytes = fileContents && (fileContents.byteLength || fileContents.length || 0)
    if (res.timings.sending > 0 && sizeBytes > 0) {
        const rate = (sizeBytes / (res.timings.sending / 1000)) / (1024 * 1024) // MB/s
        upload_rate_mb_s.add(rate)
        if (res.timings.sending > 3000) {
            console.warn(`Upload lento: sending=${res.timings.sending} ms, size=${(sizeBytes/1024/1024).toFixed(2)} MB, rate=${rate.toFixed(2)} MB/s`)
        }
    }

    check(res, {
        'upload status ok': (r) => r.status === 201,
    })

}
