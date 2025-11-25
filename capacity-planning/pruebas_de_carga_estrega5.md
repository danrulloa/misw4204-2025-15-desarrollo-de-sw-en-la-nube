https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Resultados-pruebas-carga-entrega-5

# 4MB
## 20:35

ubuntu@ip-172-31-65-7:~$ k6 run 0unaPeticion.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 0unaPeticion.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 1 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 1       23.998469/s
    checks_succeeded...: 100.00% 1 out of 1
    checks_failed......: 0.00%   0 out of 1

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=29.64ms min=29.64ms med=29.64ms max=29.64ms p(90)=29.64ms p(95)=29.64ms
      { expected_response:true }...: avg=29.64ms min=29.64ms med=29.64ms max=29.64ms p(90)=29.64ms p(95)=29.64ms
    http_req_failed................: 0.00%  0 out of 1
    http_reqs......................: 1      23.998469/s

    EXECUTION
    iteration_duration.............: avg=41.54ms min=41.54ms med=41.54ms max=41.54ms p(90)=41.54ms p(95)=41.54ms
    iterations.....................: 1      23.998469/s

    NETWORK
    data_received..................: 360 B  8.6 kB/s
    data_sent......................: 3.6 MB 87 MB/s
`



running (00m00.0s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m00.0s/10m0s  1/1 shared iters

## 20:39
ubuntu@ip-172-31-65-7:~$ k6 run 1sanidad.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<5000' p(95)=225.97ms

    http_req_sending
    ✓ 'p(95)<3000' p(95)=6.22ms

    http_req_waiting
    ✓ 'p(95)<4000' p(95)=221.36ms


  █ TOTAL RESULTS

    checks_total.......: 1083    18.015481/s
    checks_succeeded...: 100.00% 1083 out of 1083
    checks_failed......: 0.00%   0 out of 1083

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.003677   avg=0.015413    med=0.007924    p(90)=0.011379    p(95)=0.019811    p(99)=0.11173  
    timing_connecting..............: min=0          avg=0.002728    med=0           p(90)=0           p(95)=0           p(99)=0        
    timing_receiving...............: min=0.038512   avg=0.851763    med=0.27852     p(90)=2.346328    p(95)=3.613292    p(99)=7.856848 
    timing_sending.................: min=1.611427   avg=3.356262    med=2.927134    p(90)=4.412721    p(95)=6.221842    p(99)=11.957715
    timing_waiting.................: min=21.599074  avg=130.489487  med=133.477402  p(90)=212.526776  p(95)=221.369963  p(99)=264.320542
    upload_rate_mb_s...............: min=135.275354 avg=1184.575214 med=1177.950849 p(90)=1660.975638 p(95)=1768.675713 p(99)=1919.574805

    HTTP
    http_req_duration..............: min=26.99ms    avg=134.69ms    med=136.74ms    p(90)=218.25ms    p(95)=225.97ms    p(99)=269.85ms 
      { expected_response:true }...: min=26.99ms    avg=134.69ms    med=136.74ms    p(90)=218.25ms    p(95)=225.97ms    p(99)=269.85ms 
    http_req_failed................: 0.00%  0 out of 1083
    http_reqs......................: 1083   18.015481/s

    EXECUTION
    iteration_duration.............: min=31.02ms    avg=138.78ms    med=141.11ms    p(90)=222.11ms    p(95)=230.87ms    p(99)=273.93ms 
    iterations.....................: 1083   18.015481/s
    vus............................: 4      min=1         max=4
    vus_max........................: 5      min=5         max=5

    NETWORK
    data_received..................: 390 kB 6.5 kB/s
    data_sent......................: 3.9 GB 65 MB/s




running (1m00.1s), 0/5 VUs, 1083 complete and 0 interrupted iterations
default ✓ [======================================] 0/5 VUs  1m0s

## 20:41
ubuntu@ip-172-31-65-7:~$ k6 run 2escalamiento.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 8m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 8m0s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<1000' p(95)=297.69ms


  █ TOTAL RESULTS

    checks_total.......: 9645    20.086472/s
    checks_succeeded...: 100.00% 9645 out of 9645
    checks_failed......: 0.00%   0 out of 9645

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.003405  avg=0.012898    med=0.007886    p(90)=0.011933    p(95)=0.017877    p(99)=0.059119  
    timing_connecting..............: min=0         avg=0.001974    med=0           p(90)=0           p(95)=0           p(99)=0         
    timing_receiving...............: min=0.026451  avg=1.718749    med=0.703531    p(90)=4.866886    p(95)=6.80743     p(99)=11.889622 
    timing_sending.................: min=1.505011  avg=4.254487    med=3.227385    p(90)=7.167727    p(95)=9.452226    p(99)=16.578403 
    timing_waiting.................: min=18.164159 avg=191.998992  med=222.71502   p(90)=276.893858  p(95)=289.658487  p(99)=383.860285
    upload_rate_mb_s...............: min=39.615085 avg=1043.970211 med=1068.363391 p(90)=1578.355557 p(95)=1713.839553 p(99)=1911.119474

    HTTP
    http_req_duration..............: min=22.06ms   avg=197.97ms    med=229.5ms     p(90)=284.13ms    p(95)=297.69ms    p(99)=389.98ms  
      { expected_response:true }...: min=22.06ms   avg=197.97ms    med=229.5ms     p(90)=284.13ms    p(95)=297.69ms    p(99)=389.98ms  
    http_req_failed................: 0.00%  0 out of 9645
    http_reqs......................: 9645   20.086472/s

    EXECUTION
    iteration_duration.............: min=24.95ms   avg=202.2ms     med=233.66ms    p(90)=288.85ms    p(95)=301.99ms    p(99)=394.65ms  
    iterations.....................: 9645   20.086472/s
    vus............................: 5      min=1         max=5
    vus_max........................: 5      min=5         max=5

    NETWORK
    data_received..................: 3.5 MB 7.2 kB/s
    data_sent......................: 35 GB  73 MB/s




running (8m00.2s), 0/5 VUs, 9645 complete and 0 interrupted iterations
default ✓ [======================================] 0/5 VUs  8m0s

## 20:51
ubuntu@ip-172-31-65-7:~$ k6 run 3sostenidaCorta.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 3sostenidaCorta.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 5m31s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 5m1s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 15324   50.87908/s
    checks_succeeded...: 100.00% 15324 out of 15324
    checks_failed......: 0.00%   0 out of 15324

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=93.91ms min=21.64ms med=63.12ms max=1.09s p(90)=190.3ms  p(95)=212.16ms
      { expected_response:true }...: avg=93.91ms min=21.64ms med=63.12ms max=1.09s p(90)=190.3ms  p(95)=212.16ms
    http_req_failed................: 0.00%  0 out of 15324
    http_reqs......................: 15324  50.87908/s

    EXECUTION
    iteration_duration.............: avg=98.06ms min=24.48ms med=67.73ms max=1.1s  p(90)=194.33ms p(95)=216.21ms
    iterations.....................: 15324  50.87908/s
    vus............................: 5      min=4          max=5
    vus_max........................: 5      min=5          max=5

    NETWORK
    data_received..................: 5.5 MB 18 kB/s
    data_sent......................: 55 GB  184 MB/s




running (5m01.2s), 0/5 VUs, 15324 complete and 0 interrupted iterations
default ✓ [======================================] 0/5 VUs  5m1s

<img width="900" height="400" alt="image" src="https://github.com/user-attachments/assets/b0aae258-3308-4d2c-9661-7408d7d997e1" />

<img width="750" height="350" alt="image" src="https://github.com/user-attachments/assets/a814af7f-89a9-4e5b-91c5-b973d5e4fe5e" />

<img width="750" height="350" alt="image" src="https://github.com/user-attachments/assets/f54857ae-1505-4164-ad38-471d74133b3f" />

<img width="750" height="350" alt="image" src="https://github.com/user-attachments/assets/f8435f83-ac6f-4560-a3eb-c169405a9b46" />

<img width="750" height="350" alt="image" src="https://github.com/user-attachments/assets/67b45ed4-ed2c-4c20-bdd8-510dd0ced247" />

<img width="1000" height="350" alt="image" src="https://github.com/user-attachments/assets/9ad56aa1-8f42-46eb-813a-3c58ca11002e" />

<img width="1802" height="824" alt="image" src="https://github.com/user-attachments/assets/20503f10-4645-4fa7-8b42-818e9ee2915a" />

<img width="2317" height="801" alt="image" src="https://github.com/user-attachments/assets/421c011b-6d68-49a2-ac3a-687b91ebe03c" />

`SELECT`
  `COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0)                              AS processed_60m_total,`
  `ROUND(COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0) / 60.0, 2)            AS avg_per_min_60m,`
  `ROUND(COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0) / 3600.0, 3)          AS avg_per_sec_60m,`

  `COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0)                               AS processed_5m_total,`
  `ROUND(COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0) / 5.0, 2)              AS avg_per_min_5m,`
  `ROUND(COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0) / 300.0, 3)            AS avg_per_sec_5m,`

  `COALESCE(SUM(CASE WHEN c.bucket = '1m' THEN c.cnt END), 0)                               AS processed_last_minute,`
  `ROUND(COALESCE(SUM(CASE WHEN c.bucket = '1m' THEN c.cnt END), 0) / 60.0, 3)             AS per_sec_last_minute`
`FROM (`
  `SELECT '60m' AS bucket, COUNT(*)::numeric AS cnt`
  `FROM videos`
  `WHERE status = 'processed'`
    `AND processed_at >= now() - interval '60 minutes'`

  `UNION ALL`

  `SELECT '5m' AS bucket, COUNT(*)::numeric AS cnt`
  `FROM videos`
  `WHERE status = 'processed'`
    `AND processed_at >= now() - interval '5 minutes'`

  `UNION ALL`

  `SELECT '1m' AS bucket, COUNT(*)::numeric AS cnt`
  `FROM videos`
  `WHERE status = 'processed'`
    `AND processed_at >= date_trunc('minute', now()) - interval '1 minute'`
    `AND processed_at <  date_trunc('minute', now())`
`) AS c;`

`{`
`"SELECT\r\n  COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0)                              AS processed_60m_total,\r\n  ROUND(COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0) \/ 60.0, 2)            AS avg_per_min_60m,\r\n  ROUND(COALESCE(SUM(CASE WHEN c.bucket = '60m' THEN c.cnt END), 0) \/ 3600.0, 3)          AS avg_per_sec_60m,\r\n\r\n  COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0)                               AS processed_5m_total,\r\n  ROUND(COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0) \/ 5.0, 2)              AS avg_per_min_5m,\r\n  ROUND(COALESCE(SUM(CASE WHEN c.bucket = '5m' THEN c.cnt END), 0) \/ 300.0, 3)            AS avg_per_sec_5m,\r\n\r\n  COALESCE(SUM(CASE WHEN c.bucket = '1m' THEN c.cnt END), 0)                               AS processed_last_minute,\r\n  ROUND(COALESCE(SUM(CASE WHEN c.bucket = '1m' THEN c.cnt END), 0) \/ 60.0, 3)             AS per_sec_last_minute\r\nFROM (\r\n  SELECT '60m' AS bucket, COUNT(*)::numeric AS cnt\r\n  FROM videos\r\n  WHERE status = 'processed'\r\n    AND processed_at >= now() - interval '60 minutes'\r\n\r\n  UNION ALL\r\n\r\n  SELECT '5m' AS bucket, COUNT(*)::numeric AS cnt\r\n  FROM videos\r\n  WHERE status = 'processed'\r\n    AND processed_at >= now() - interval '5 minutes'\r\n\r\n  UNION ALL\r\n\r\n  SELECT '1m' AS bucket, COUNT(*)::numeric AS cnt\r\n  FROM videos\r\n  WHERE status = 'processed'\r\n    AND processed_at >= date_trunc('minute', now()) - interval '1 minute'\r\n    AND processed_at <  date_trunc('minute', now())\r\n) AS c": [`
	`{`
		`"processed_60m_total" : 695,`
		`"avg_per_min_60m" : 11.58,`
		`"avg_per_sec_60m" : 0.193,`
		`"processed_5m_total" : 695,`
		`"avg_per_min_5m" : 139.00,`
		`"avg_per_sec_5m" : 2.317,`
		`"processed_last_minute" : 0,`
		`"per_sec_last_minute" : 0.000`
	`}`
`]}`


|processed_60m_total|avg_per_min_60m|avg_per_sec_60m|processed_5m_total|avg_per_min_5m|avg_per_sec_5m|processed_last_minute|per_sec_last_minute|
|-------------------|---------------|---------------|------------------|--------------|--------------|---------------------|-------------------|
|1.733              |28,88          |0,481          |1.733             |346,6         |5,777         |0                    |0                  |

# 50MB
## 22:00
ubuntu@ip-172-31-65-7:~$ k6 run 0unaPeticion.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 0unaPeticion.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 1 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 1       1.66976/s
    checks_succeeded...: 100.00% 1 out of 1
    checks_failed......: 0.00%   0 out of 1

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=479.02ms min=479.02ms med=479.02ms max=479.02ms p(90)=479.02ms p(95)=479.02ms
      { expected_response:true }...: avg=479.02ms min=479.02ms med=479.02ms max=479.02ms p(90)=479.02ms p(95)=479.02ms
    http_req_failed................: 0.00% 0 out of 1
    http_reqs......................: 1     1.66976/s

    EXECUTION
    iteration_duration.............: avg=598.74ms min=598.74ms med=598.74ms max=598.74ms p(90)=598.74ms p(95)=598.74ms
    iterations.....................: 1     1.66976/s

    NETWORK
    data_received..................: 360 B 601 B/s
    data_sent......................: 51 MB 85 MB/s




running (00m00.6s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m00.6s/10m0s  1/1 shared iters

## 22:05
ubuntu@ip-172-31-65-7:~$ k6 run 1sanidad.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<5000' p(95)=1.9s

    http_req_sending
    ✓ 'p(95)<3000' p(95)=1.41s

    http_req_waiting
    ✓ 'p(95)<4000' p(95)=604.6ms


  █ TOTAL RESULTS

    checks_total.......: 134     2.204155/s
    checks_succeeded...: 100.00% 134 out of 134
    checks_failed......: 0.00%   0 out of 134

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.004336   avg=0.070639   med=0.009876   p(90)=0.015288    p(95)=0.034939    p(99)=1.928529
    timing_connecting..............: min=0          avg=0.042633   med=0          p(90)=0           p(95)=0           p(99)=0.597742
    timing_receiving...............: min=0.049162   avg=0.210693   med=0.14407    p(90)=0.370835    p(95)=0.453213    p(99)=1.090619
    timing_sending.................: min=117.399112 avg=797.623203 med=704.10034  p(90)=1318.658444 p(95)=1411.666742 p(99)=1450.45879
    timing_waiting.................: min=90.946705  avg=269.123285 med=241.375526 p(90)=487.196723  p(95)=604.603058  p(99)=737.756689
    upload_rate_mb_s...............: min=30.611124  avg=80.522028  med=68.767718  p(90)=147.451269  p(95)=153.653178  p(99)=166.276236

    HTTP
    http_req_duration..............: min=208.44ms   avg=1.06s      med=1.01s      p(90)=1.72s       p(95)=1.9s        p(99)=2.01s
      { expected_response:true }...: min=208.44ms   avg=1.06s      med=1.01s      p(90)=1.72s       p(95)=1.9s        p(99)=2.01s
    http_req_failed................: 0.00%  0 out of 134
    http_reqs......................: 134    2.204155/s

    EXECUTION
    iteration_duration.............: min=358.6ms    avg=1.13s      med=1.05s      p(90)=1.79s       p(95)=1.94s       p(99)=2.09s
    iterations.....................: 134    2.204155/s
    vus............................: 4      min=1        max=4
    vus_max........................: 5      min=5        max=5

    NETWORK
    data_received..................: 48 kB  794 B/s
    data_sent......................: 6.8 GB 112 MB/s




running (1m00.8s), 0/5 VUs, 134 complete and 0 interrupted iterations
default ✓ [======================================] 0/5 VUs  1m0s

## 22:45


ubuntu@ip-172-31-65-7:~$ k6 run 2escalamiento.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 8m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 8m0s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)

Killed

<img width="2329" height="507" alt="image" src="https://github.com/user-attachments/assets/50f42722-5add-42e8-8414-cc386033948e" />

<img width="2062" height="757" alt="image" src="https://github.com/user-attachments/assets/1e4937dd-3d24-47d6-baac-6c69543b2783" />

<img width="2049" height="710" alt="image" src="https://github.com/user-attachments/assets/c3fcf5e3-940d-441a-b91b-616f82703f04" />

<img width="2075" height="758" alt="image" src="https://github.com/user-attachments/assets/e879fcbe-14eb-425e-90c2-d96e2faeb510" />

<img width="2025" height="609" alt="image" src="https://github.com/user-attachments/assets/bbd6cb0e-f7ec-4a26-9418-5c7df0e5ccda" />

<img width="1737" height="785" alt="image" src="https://github.com/user-attachments/assets/158ce4a9-b2ee-414f-b344-f9166638f6a6" />

<img width="2293" height="753" alt="image" src="https://github.com/user-attachments/assets/dbcaa397-79e8-40f6-acf3-6e50843e3a40" />

|processed_60m_total|avg_per_min_60m|avg_per_sec_60m|processed_5m_total|avg_per_min_5m|avg_per_sec_5m|processed_last_minute|per_sec_last_minute|
|-------------------|---------------|---------------|------------------|--------------|--------------|---------------------|-------------------|
|1.301              |21,68          |0,361          |1.301             |260,2         |4,337         |0                    |0                  |

ubuntu@ip-172-31-65-7:~$ k6 run --vus 2 --duration 8m 2escalamiento.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 2 max VUs, 8m30s max duration (incl. graceful stop):
              * default: 2 looping VUs for 8m0s (gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✗ 'p(95)<1000' p(95)=1.16s


  █ TOTAL RESULTS

    checks_total.......: 896     1.865429/s
    checks_succeeded...: 100.00% 896 out of 896
    checks_failed......: 0.00%   0 out of 896

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.002814   avg=0.031835   med=0.009664   p(90)=0.013517   p(95)=0.017496   p(99)=0.073531
    timing_connecting..............: min=0          avg=0.001411   med=0          p(90)=0          p(95)=0          p(99)=0
    timing_receiving...............: min=0.039992   avg=0.173178   med=0.125233   p(90)=0.282295   p(95)=0.346669   p(99)=0.614565
    timing_sending.................: min=137.645703 avg=818.054784 med=903.516605 p(90)=962.837159 p(95)=980.228313 p(99)=1027.848788
    timing_waiting.................: min=119.424734 avg=176.676212 med=173.847615 p(90)=192.790219 p(95)=204.163279 p(99)=326.947874
    upload_rate_mb_s...............: min=45.186832  avg=74.221144  med=53.589616  p(90)=117.210029 p(95)=244.474565 p(99)=284.477682

    HTTP
    http_req_duration..............: min=287.75ms   avg=994.9ms    med=1.07s      p(90)=1.14s      p(95)=1.16s      p(99)=1.21s
      { expected_response:true }...: min=287.75ms   avg=994.9ms    med=1.07s      p(90)=1.14s      p(95)=1.16s      p(99)=1.21s
    http_req_failed................: 0.00%  0 out of 896
    http_reqs......................: 896    1.865429/s

    EXECUTION
    iteration_duration.............: min=326.83ms   avg=1.07s      med=1.15s      p(90)=1.2s       p(95)=1.22s      p(99)=1.29s
    iterations.....................: 896    1.865429/s
    vus............................: 2      min=2        max=2
    vus_max........................: 2      min=2        max=2

    NETWORK
    data_received..................: 323 kB 672 B/s
    data_sent......................: 46 GB  95 MB/s




running (8m00.3s), 0/2 VUs, 896 complete and 0 interrupted iterations
default ✓ [======================================] 2 VUs  8m0s
ERRO[0481] thresholds on metrics 'http_req_duration' have been crossed

## 23:11
ubuntu@ip-172-31-65-7:~$ k6 run --vus 2 --duration 5m 3sostenidaCorta.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 3sostenidaCorta.js
        output: -

     scenarios: (100.00%) 1 scenario, 2 max VUs, 5m30s max duration (incl. graceful stop):
              * default: 2 looping VUs for 5m0s (gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 1463    4.867787/s
    checks_succeeded...: 100.00% 1463 out of 1463
    checks_failed......: 0.00%   0 out of 1463

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=356.09ms min=192.26ms med=257.26ms max=877.58ms p(90)=616.63ms p(95)=639.73ms
      { expected_response:true }...: avg=356.09ms min=192.26ms med=257.26ms max=877.58ms p(90)=616.63ms p(95)=639.73ms
    http_req_failed................: 0.00%  0 out of 1463
    http_reqs......................: 1463   4.867787/s

    EXECUTION
    iteration_duration.............: avg=410.47ms min=227.92ms med=323.58ms max=916.55ms p(90)=665.27ms p(95)=686.28ms
    iterations.....................: 1463   4.867787/s
    vus............................: 2      min=2         max=2
    vus_max........................: 2      min=2         max=2

    NETWORK
    data_received..................: 527 kB 1.8 kB/s
    data_sent......................: 74 GB  247 MB/s




running (5m00.5s), 0/2 VUs, 1463 complete and 0 interrupted iterations
default ✓ [======================================] 2 VUs  5m0s

|processed_60m_total|avg_per_min_60m|avg_per_sec_60m|processed_5m_total|avg_per_min_5m|avg_per_sec_5m|processed_last_minute|per_sec_last_minute|
|-------------------|---------------|---------------|------------------|--------------|--------------|---------------------|-------------------|
|1.689              |28,15          |0,469          |1.689             |337,8         |5,63          |0                    |0                  |

<img width="2320" height="495" alt="image" src="https://github.com/user-attachments/assets/1be500d0-5f4c-4754-bba9-165627c9486a" />

<img width="2043" height="740" alt="image" src="https://github.com/user-attachments/assets/6b9d3c24-efdd-4433-b434-88d6eddd9583" />

<img width="2023" height="511" alt="image" src="https://github.com/user-attachments/assets/aebfc059-5621-4727-8cd2-3701f6cf643e" />

<img width="2028" height="567" alt="image" src="https://github.com/user-attachments/assets/a465b306-33c6-48d0-aaef-bc1520f9f16c" />

<img width="2016" height="612" alt="image" src="https://github.com/user-attachments/assets/3047bd85-f72b-4909-a856-0b24673c1108" />

<img width="1741" height="788" alt="image" src="https://github.com/user-attachments/assets/84f87b44-331b-40af-9523-379e5087618d" />

<img width="1736" height="821" alt="image" src="https://github.com/user-attachments/assets/fe95a4d8-26df-462b-a76c-41d41e95f57e" />

<img width="2257" height="691" alt="image" src="https://github.com/user-attachments/assets/8ebdae21-5146-43b1-95d7-66ed68710fd6" />

<img width="1299" height="752" alt="image" src="https://github.com/user-attachments/assets/12873110-034d-4b25-9f3f-c2118af1826b" />

# 50MB Segundo intento
## 21:35

ubuntu@ip-172-31-69-252:~$ k6 run 0unaPeticion.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 0unaPeticion.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 1 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 1       2.278522/s
    checks_succeeded...: 100.00% 1 out of 1
    checks_failed......: 0.00%   0 out of 1

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=268.19ms min=268.19ms med=268.19ms max=268.19ms p(90)=268.19ms p(95)=268.19ms
      { expected_response:true }...: avg=268.19ms min=268.19ms med=268.19ms max=268.19ms p(90)=268.19ms p(95)=268.19ms
    http_req_failed................: 0.00% 0 out of 1
    http_reqs......................: 1     2.278522/s

    EXECUTION
    iteration_duration.............: avg=438.74ms min=438.74ms med=438.74ms max=438.74ms p(90)=438.74ms p(95)=438.74ms
    iterations.....................: 1     2.278522/s

    NETWORK
    data_received..................: 360 B 820 B/s
    data_sent......................: 51 MB 116 MB/s




running (00m00.4s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m00.4s/10m0s  1/1 shared iters

ubuntu@ip-172-31-69-252:~$ k6 run 1sanidad.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<5000' p(95)=2.21s

    http_req_sending
    ✓ 'p(95)<3000' p(95)=1.81s

    http_req_waiting
    ✓ 'p(95)<4000' p(95)=727.09ms


  █ TOTAL RESULTS

    checks_total.......: 105     1.725988/s
    checks_succeeded...: 100.00% 105 out of 105
    checks_failed......: 0.00%   0 out of 105

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.007309   avg=0.173043   med=0.011596   p(90)=0.292979    p(95)=0.937428   p(99)=1.798771
    timing_connecting..............: min=0          avg=0.025971   med=0          p(90)=0           p(95)=0          p(99)=0.627353
    timing_receiving...............: min=0.040571   avg=0.401715   med=0.119596   p(90)=0.595226    p(95)=1.469046   p(99)=5.746592
    timing_sending.................: min=174.817626 avg=952.260052 med=868.787357 p(90)=1738.255767 p(95)=1814.23431 p(99)=1893.328712
    timing_waiting.................: min=53.038507  avg=325.353981 med=220.027141 p(90)=635.263249  p(95)=727.099422 p(99)=1288.225827
    upload_rate_mb_s...............: min=25.538321  avg=65.759206  med=55.731827  p(90)=114.080364  p(95)=131.40449  p(99)=141.724676

    HTTP
    http_req_duration..............: min=272.55ms   avg=1.27s      med=1.2s       p(90)=2.15s       p(95)=2.21s      p(99)=2.32s
      { expected_response:true }...: min=272.55ms   avg=1.27s      med=1.2s       p(90)=2.15s       p(95)=2.21s      p(99)=2.32s
    http_req_failed................: 0.00%  0 out of 105
    http_reqs......................: 105    1.725988/s

    EXECUTION
    iteration_duration.............: min=515.01ms   avg=1.45s      med=1.41s      p(90)=2.32s       p(95)=2.42s      p(99)=2.48s
    iterations.....................: 105    1.725988/s
    vus............................: 4      min=1        max=4
    vus_max........................: 5      min=5        max=5

    NETWORK
    data_received..................: 38 kB  621 B/s
    data_sent......................: 5.3 GB 88 MB/s




running (1m00.8s), 0/5 VUs, 105 complete and 0 interrupted iterations
default ✓ [======================================] 0/5 VUs  1m0s

ubuntu@ip-172-31-69-252:~$ k6 run 2escalamiento.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 8m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 8m0s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)

WARN[0224] Upload lento: sending=5696.691095 ms, size=48.42 MB, rate=8.50 MB/s  source=console
WARN[0224] Upload lento: sending=5714.130558 ms, size=48.42 MB, rate=8.47 MB/s  source=console
WARN[0224] Upload lento: sending=19038.828718 ms, size=48.42 MB, rate=2.54 MB/s  source=console
WARN[0224] Upload lento: sending=19294.412391 ms, size=48.42 MB, rate=2.51 MB/s  source=console
WARN[0224] Upload lento: sending=19113.719469 ms, size=48.42 MB, rate=2.53 MB/s  source=console
WARN[0242] Upload lento: sending=5876.930179 ms, size=48.42 MB, rate=8.24 MB/s  source=console
WARN[0242] Upload lento: sending=3704.245037 ms, size=48.42 MB, rate=13.07 MB/s  source=console
WARN[0243] Upload lento: sending=7034.3786 ms, size=48.42 MB, rate=6.88 MB/s  source=console
WARN[0243] Upload lento: sending=5066.369238 ms, size=48.42 MB, rate=9.56 MB/s  source=console
WARN[0356] Request Failed                                error="Post \"http://anb-alb-340855830.us-east-1.elb.amazonaws.com/api/videos/upload\": write tcp 172.31.69.252:35392->3.209.28.40:80: use of closed network connection"
WARN[0371] Upload lento: sending=99741.651974 ms, size=48.42 MB, rate=0.49 MB/s  source=console
WARN[0371] Upload lento: sending=126154.974377 ms, size=48.42 MB, rate=0.38 MB/s  source=console
WARN[0371] Upload lento: sending=8184.881389 ms, size=48.42 MB, rate=5.92 MB/s  source=console
WARN[0446] Request Failed                                error="Post \"http://anb-alb-340855830.us-east-1.elb.amazonaws.com/api/videos/upload\": http: server closed idle connection"


  █ THRESHOLDS

    http_req_duration
    ✗ 'p(95)<1000' p(95)=2.96s


  █ TOTAL RESULTS

    checks_total.......: 344    0.619441/s
    checks_succeeded...: 99.70% 343 out of 344
    checks_failed......: 0.29%  1 out of 344

    ✗ upload status ok
      ↳  99% — ✓ 343 / ✗ 1

    CUSTOM
    timing_blocked.................: min=0.003612 avg=79.246998  med=0.011106    p(90)=0.034099    p(95)=0.713587    p(99)=280.473381
    timing_connecting..............: min=0        avg=0.204989   med=0           p(90)=0           p(95)=0           p(99)=2.590832
    timing_receiving...............: min=0        avg=103.559833 med=0.147553    p(90)=6.492131    p(95)=13.345924   p(99)=1159.8007
    timing_sending.................: min=0        avg=2123.10978 med=1235.786173 p(90)=2006.307603 p(95)=2419.201927 p(99)=19081.516446
    timing_waiting.................: min=0        avg=328.948164 med=229.757155  p(90)=699.584178  p(95)=930.476239  p(99)=1567.212585
    upload_rate_mb_s...............: min=0.383807 avg=52.456901  med=38.660185   p(90)=107.205188  p(95)=108.934709  p(99)=119.615095

    HTTP
    http_req_duration..............: min=0s       avg=2.76s      med=1.64s       p(90)=2.69s       p(95)=2.96s       p(99)=19.73s
      { expected_response:true }...: min=315.96ms avg=2.78s      med=1.64s       p(90)=2.7s        p(95)=2.97s       p(99)=19.73s
    http_req_failed................: 0.57%  2 out of 346
    http_reqs......................: 346    0.623042/s

    EXECUTION
    iteration_duration.............: min=452.87ms avg=4.08s      med=1.7s        p(90)=2.79s       p(95)=3.36s       p(99)=2m6s
    iterations.....................: 344    0.619441/s
    vus............................: 5      min=1        max=5
    vus_max........................: 5      min=5        max=5

    NETWORK
    data_received..................: 124 kB 224 B/s
    data_sent......................: 18 GB  32 MB/s




running (9m15.3s), 0/5 VUs, 344 complete and 5 interrupted iterations
default ✓ [======================================] 5/5 VUs  8m0s
ERRO[0556] thresholds on metrics 'http_req_duration' have been crossed

ubuntu@ip-172-31-69-252:~$ k6 run 3sostenidaCorta.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 3sostenidaCorta.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 5m31s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 5m1s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)

WARN[0086] Request Failed                                error="Post \"http://anb-alb-340855830.us-east-1.elb.amazonaws.com/api/videos/upload\": write tcp 172.31.69.252:50336->98.95.44.72:80: use of closed network connection"


  █ TOTAL RESULTS

    checks_total.......: 73     0.215139/s
    checks_succeeded...: 98.63% 72 out of 73
    checks_failed......: 1.36%  1 out of 73

    ✗ upload status ok
      ↳  98% — ✓ 72 / ✗ 1

    HTTP
    http_req_duration..............: avg=7.21s  min=0s       med=2.32s max=1m17s p(90)=35.52s p(95)=42.77s
      { expected_response:true }...: avg=7.31s  min=205.96ms med=2.34s max=1m17s p(90)=37.87s p(95)=42.82s
    http_req_failed................: 1.36%  1 out of 73
    http_reqs......................: 73     0.215139/s

    EXECUTION
    iteration_duration.............: avg=16.61s min=299.79ms med=2.44s max=3m32s p(90)=59.39s p(95)=1m33s
    iterations.....................: 73     0.215139/s
    vus............................: 4      min=4       max=5
    vus_max........................: 5      min=5       max=5

    NETWORK
    data_received..................: 26 kB  77 B/s
    data_sent......................: 3.7 GB 11 MB/s




running (5m39.3s), 0/5 VUs, 72 complete and 5 interrupted iterations
default ✓ [======================================] 5/5 VUs  5m1s

<img width="2338" height="506" alt="image" src="https://github.com/user-attachments/assets/0de63f95-ce29-4d01-93f1-7000a53b1b69" />

<img width="2064" height="512" alt="image" src="https://github.com/user-attachments/assets/3e36dc32-a40f-4164-bcc9-efa8d718911c" />

<img width="2069" height="328" alt="image" src="https://github.com/user-attachments/assets/19ecc98d-9b7e-46ba-b9c2-35c340c86c78" />

<img width="2046" height="513" alt="image" src="https://github.com/user-attachments/assets/cd5f9ea9-2ad7-4478-98c8-d3d3979e914d" />

<img width="2059" height="487" alt="image" src="https://github.com/user-attachments/assets/bf319939-8e34-4474-a493-4cb3745ac725" />

### RDS
<img width="2304" height="757" alt="image" src="https://github.com/user-attachments/assets/93d19df4-c705-4588-b3dd-d5ef0f92f9c3" />
![ALB50MB_page-0001](https://github.com/user-attachments/assets/38d90ec8-2fff-4188-9e82-aa903d2e6c03)

<img width="1805" height="778" alt="image" src="https://github.com/user-attachments/assets/d60c5e87-0bfb-4bb2-9849-35a4473f1926" />
<img width="1810" height="808" alt="image" src="https://github.com/user-attachments/assets/6bfd73fa-0f47-48ce-b271-b14abd98d84f" />
<img width="1795" height="782" alt="image" src="https://github.com/user-attachments/assets/97fd4775-d628-4c4f-93c3-019c1c9b05eb" />



|processed_60m_total|avg_per_min_60m|avg_per_sec_60m|processed_5m_total|avg_per_min_5m|avg_per_sec_5m|processed_last_minute|per_sec_last_minute|
|-------------------|---------------|---------------|------------------|--------------|--------------|---------------------|-------------------|
|486                |8,1            |0,135          |486               |97,2          |1,62          |0                    |0                  |


# 96MB
## 22:35

ubuntu@ip-172-31-69-252:~$ k6 run 0unaPeticion.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 0unaPeticion.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 1 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 1       1.961052/s
    checks_succeeded...: 100.00% 1 out of 1
    checks_failed......: 0.00%   0 out of 1

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=300.54ms min=300.54ms med=300.54ms max=300.54ms p(90)=300.54ms p(95)=300.54ms
      { expected_response:true }...: avg=300.54ms min=300.54ms med=300.54ms max=300.54ms p(90)=300.54ms p(95)=300.54ms
    http_req_failed................: 0.00% 0 out of 1
    http_reqs......................: 1     1.961052/s

    EXECUTION
    iteration_duration.............: avg=509.74ms min=509.74ms med=509.74ms max=509.74ms p(90)=509.74ms p(95)=509.74ms
    iterations.....................: 1     1.961052/s

    NETWORK
    data_received..................: 360 B 706 B/s
    data_sent......................: 99 MB 194 MB/s




running (00m00.5s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m00.5s/10m0s  1/1 shared iters

ubuntu@ip-172-31-69-252:~$ k6 run 1sanidad.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 5 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 5 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)

Killed

ubuntu@ip-172-31-69-252:~$ k6 run 1sanidad.js----] 2/5 VUs  0m17.2s/1m00.0s

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 4 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 4 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)

Killed

ubuntu@ip-172-31-69-252:~$ k6 run 1sanidad.js interrupted iterations

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 3 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 3 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)

Killed

ubuntu@ip-172-31-69-252:~$ k6 run 1sanidad.js interrupted iterations

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 1sanidad.js
        output: -

     scenarios: (100.00%) 1 scenario, 2 max VUs, 1m30s max duration (incl. graceful stop):
              * default: Up to 2 looping VUs for 1m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<5000' p(95)=693.78ms

    http_req_sending
    ✓ 'p(95)<3000' p(95)=595.57ms

    http_req_waiting
    ✓ 'p(95)<4000' p(95)=102.51ms


  █ TOTAL RESULTS

    checks_total.......: 85      1.404218/s
    checks_succeeded...: 100.00% 85 out of 85
    checks_failed......: 0.00%   0 out of 85

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.006966   avg=0.090724   med=0.009839   p(90)=0.011633   p(95)=0.013328   p(99)=1.173647
    timing_connecting..............: min=0          avg=0.007615   med=0          p(90)=0          p(95)=0          p(99)=0.103559
    timing_receiving...............: min=0.056899   avg=0.096254   med=0.080997   p(90)=0.143394   p(95)=0.165828   p(99)=0.283636
    timing_sending.................: min=184.940239 avg=516.312324 med=534.710474 p(90)=564.437684 p(95)=595.578106 p(99)=634.757324
    timing_waiting.................: min=71.161351  avg=90.560304  med=91.907301  p(90)=99.784156  p(95)=102.51271  p(99)=107.317108
    upload_rate_mb_s...............: min=145.88237  avg=187.194741 med=176.203989 p(90)=212.776822 p(95)=234.683964 p(99)=294.622332

    HTTP
    http_req_duration..............: min=256.21ms   avg=606.96ms   med=627.28ms   p(90)=655.08ms   p(95)=693.78ms   p(99)=725.7ms
      { expected_response:true }...: min=256.21ms   avg=606.96ms   med=627.28ms   p(90)=655.08ms   p(95)=693.78ms   p(99)=725.7ms
    http_req_failed................: 0.00%  0 out of 85
    http_reqs......................: 85     1.404218/s

    EXECUTION
    iteration_duration.............: min=506.51ms   avg=712.1ms    med=708.19ms   p(90)=758.89ms   p(95)=778.91ms   p(99)=794.99ms
    iterations.....................: 85     1.404218/s
    vus............................: 1      min=1       max=1
    vus_max........................: 2      min=2       max=2

    NETWORK
    data_received..................: 31 kB  506 B/s
    data_sent......................: 8.4 GB 139 MB/s




running (1m00.5s), 0/2 VUs, 85 complete and 0 interrupted iterations
default ✓ [======================================] 0/2 VUs  1m0s

ubuntu@ip-172-31-69-252:~$ k6 run 2escalamiento.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 2 max VUs, 8m30s max duration (incl. graceful stop):
              * default: Up to 2 looping VUs for 8m0s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)

Killed
ubuntu@ip-172-31-69-252:~$ k6 run 2escalamiento.jserrupted iterations

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 2escalamiento.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 8m30s max duration (incl. graceful stop):
              * default: Up to 1 looping VUs for 8m0s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<1000' p(95)=693.25ms


  █ TOTAL RESULTS

    checks_total.......: 868     1.806903/s
    checks_succeeded...: 100.00% 868 out of 868
    checks_failed......: 0.00%   0 out of 868

    ✓ upload status ok

    CUSTOM
    timing_blocked.................: min=0.006307   avg=0.032039   med=0.010054   p(90)=0.011414   p(95)=0.012003   p(99)=0.062948
    timing_connecting..............: min=0          avg=0.000669   med=0          p(90)=0          p(95)=0          p(99)=0
    timing_receiving...............: min=0.055669   avg=0.111674   med=0.084038   p(90)=0.19112    p(95)=0.280102   p(99)=0.36387
    timing_sending.................: min=158.29945  avg=359.399235 med=443.994195 p(90)=547.05619  p(95)=557.893269 p(99)=608.775434
    timing_waiting.................: min=65.746664  avg=108.489609 med=99.919562  p(90)=142.810437 p(95)=145.087334 p(99)=156.469646
    upload_rate_mb_s...............: min=119.479224 avg=344.100361 med=212.206016 p(90)=567.217843 p(95)=577.528083 p(99)=588.958188

    HTTP
    http_req_duration..............: min=239.79ms   avg=468ms      med=574.06ms   p(90)=682.48ms   p(95)=693.25ms   p(99)=758.96ms
      { expected_response:true }...: min=239.79ms   avg=468ms      med=574.06ms   p(90)=682.48ms   p(95)=693.25ms   p(99)=758.96ms
    http_req_failed................: 0.00%  0 out of 868
    http_reqs......................: 868    1.806903/s

    EXECUTION
    iteration_duration.............: min=309.65ms   avg=553.41ms   med=667.97ms   p(90)=758.36ms   p(95)=769.96ms   p(99)=837.66ms
    iterations.....................: 868    1.806903/s
    vus............................: 1      min=1        max=1
    vus_max........................: 1      min=1        max=1

    NETWORK
    data_received..................: 313 kB 651 B/s
    data_sent......................: 86 GB  179 MB/s




running (8m00.4s), 0/1 VUs, 868 complete and 0 interrupted iterations
default ✓ [======================================] 0/1 VUs  8m0s

ubuntu@ip-172-31-69-252:~$ k6 run 3sostenidaCorta.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 3sostenidaCorta.js
        output: -

     scenarios: (100.00%) 1 scenario, 2 max VUs, 5m31s max duration (incl. graceful stop):
              * default: Up to 2 looping VUs for 5m1s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)



  █ TOTAL RESULTS

    checks_total.......: 557     1.846477/s
    checks_succeeded...: 100.00% 557 out of 557
    checks_failed......: 0.00%   0 out of 557

    ✓ upload status ok

    HTTP
    http_req_duration..............: avg=450.03ms min=237.25ms med=448.77ms max=806.45ms p(90)=676.6ms  p(95)=693.58ms
      { expected_response:true }...: avg=450.03ms min=237.25ms med=448.77ms max=806.45ms p(90)=676.6ms  p(95)=693.58ms
    http_req_failed................: 0.00%  0 out of 557
    http_reqs......................: 557    1.846477/s

    EXECUTION
    iteration_duration.............: avg=541.55ms min=307.6ms  med=555.2ms  max=989.34ms p(90)=753.57ms p(95)=768.5ms
    iterations.....................: 557    1.846477/s
    vus............................: 1      min=1        max=1
    vus_max........................: 2      min=2        max=2

    NETWORK
    data_received..................: 201 kB 665 B/s
    data_sent......................: 55 GB  182 MB/s




running (5m01.7s), 0/2 VUs, 557 complete and 0 interrupted iterations
default ✓ [======================================] 0/2 VUs  5m1s

ubuntu@ip-172-31-69-252:~$ k6 run 3sostenidaCorta.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: 3sostenidaCorta.js
        output: -

     scenarios: (100.00%) 1 scenario, 3 max VUs, 5m31s max duration (incl. graceful stop):
              * default: Up to 3 looping VUs for 5m1s over 2 stages (gracefulRampDown: 30s, gracefulStop: 30s)

<img width="2344" height="510" alt="image" src="https://github.com/user-attachments/assets/8013837b-7ad3-4841-8e08-c11ea8a4afdc" />

![ALB96MB_page-0001](https://github.com/user-attachments/assets/f56891bf-fb6b-4b7b-a5f0-d44d080b2a88)

<img width="2035" height="419" alt="image" src="https://github.com/user-attachments/assets/fd21196b-9399-41cf-a5c3-c9472edfe557" />

<img width="2066" height="452" alt="image" src="https://github.com/user-attachments/assets/b3fe741a-98e7-472c-915e-d2d5a27e1658" />

<img width="2024" height="463" alt="image" src="https://github.com/user-attachments/assets/1c972041-1a98-43c2-8df5-291d0cee4779" />

<img width="2057" height="479" alt="image" src="https://github.com/user-attachments/assets/80d5bd56-97cc-487e-8e74-663bd2a945fe" />

<img width="2365" height="761" alt="image" src="https://github.com/user-attachments/assets/1ddfc57b-ab82-473b-930b-eb783b664404" />

|processed_60m_total|avg_per_min_60m|avg_per_sec_60m|processed_5m_total|avg_per_min_5m|avg_per_sec_5m|processed_last_minute|per_sec_last_minute|
|-------------------|---------------|---------------|------------------|--------------|--------------|---------------------|-------------------|
|784                |13,07          |0,218          |784               |156,8         |2,613         |0                    |0                  |




