from celery import shared_task
import subprocess
import tempfile
import os
import shutil
import logging
from pathlib import Path
import psycopg
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Constant for mapping uploaded API path to worker storage
MNT_UPLOADS_PREFIX = '/mnt/uploads'


def _extract_task_self_and_args(bound_self, args):
    """Return (task_self, args) where a provided mock self is normalized out of args.

    Tests often call task.run(self_mock, ...). If args[0] has a `retry`
    attribute we treat it as a task-like object and use it for retry calls.
    """
    if args and hasattr(args[0], "retry"):
        return args[0], args[1:]
    return bound_self, args


def _parse_task_args(args, kwargs):
    """Return (video_id, input_path, correlation_id).

    Strict: expects three positional arguments (video_id, input_path, correlation_id).
    No fallbacks to kwargs are used.
    """
    if len(args) < 3:
        raise ValueError('process_video: expected three positional arguments (video_id, input_path, correlation_id)')
    return args[0], args[1], args[2]


def _is_s3_path(path: str) -> bool:
    """Detecta si la ruta es S3 (s3://bucket/key) o local."""
    return str(path).startswith('s3://')


def _parse_s3_path(s3_path: str) -> tuple[str, str]:
    """Parsea s3://bucket/key -> (bucket, key)"""
    if not _is_s3_path(s3_path):
        raise ValueError(f"Not an S3 path: {s3_path}")
    # s3://bucket/key -> bucket, key
    parts = s3_path.replace('s3://', '').split('/', 1)
    return parts[0], parts[1] if len(parts) > 1 else ''


def _make_s3_client():
    """Crea un cliente S3 alineado con el adapter del core, usando credenciales explícitas.

    - Requiere: S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - Opcionales: AWS_SESSION_TOKEN, S3_ENDPOINT_URL, S3_FORCE_PATH_STYLE, S3_VERIFY_SSL
    """
    s3_region = os.getenv('S3_REGION')
    endpoint_url = os.getenv('S3_ENDPOINT_URL')
    force_path_style = bool(int(os.getenv('S3_FORCE_PATH_STYLE', '0')))
    verify_ssl = bool(int(os.getenv('S3_VERIFY_SSL', '1')))

    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    session_token = os.getenv('AWS_SESSION_TOKEN')

    missing = []
    if not s3_region:
        missing.append('S3_REGION')
    if not access_key:
        missing.append('AWS_ACCESS_KEY_ID')
    if not secret_key:
        missing.append('AWS_SECRET_ACCESS_KEY')
    if missing:
        raise RuntimeError(f"Configuración S3/AWS incompleta: falta(n) {', '.join(missing)}")

    config = Config(s3={'addressing_style': 'path'} if force_path_style else {})
    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=s3_region,
        endpoint_url=endpoint_url,
        config=config,
        verify=verify_ssl,
    )


def _download_from_s3(s3_path: str, local_path: Path) -> Path:
    """Descarga archivo desde S3 a path local. Retorna Path local."""
    bucket, key = _parse_s3_path(s3_path)
    s3_client = _make_s3_client()

    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        s3_client.download_file(bucket, key, str(local_path))
        logger.info('Descargado desde S3: %s -> %s', s3_path, local_path)
        return local_path
    except ClientError as e:
        logger.error('Error descargando desde S3: %s', e)
        raise FileNotFoundError(f'No se pudo descargar desde S3: {s3_path}') from e


def _upload_to_s3(local_path: Path, s3_path: str) -> str:
    """Sube archivo local a S3. Retorna ruta S3."""
    bucket, key = _parse_s3_path(s3_path)
    s3_client = _make_s3_client()

    try:
        s3_client.upload_file(str(local_path), bucket, key)
        logger.info('Subido a S3: %s -> %s', local_path, s3_path)
        return s3_path
    except ClientError as e:
        logger.error('Error subiendo a S3: %s', e)
        raise RuntimeError(f'No se pudo subir a S3: {s3_path}') from e


def _resolve_worker_path(original_input):
    """Return Path para worker-local source, descargando desde S3 si es necesario."""
    if _is_s3_path(original_input):
        # Es S3: descargar a temp local
        # Usar un nombre de archivo temporal basado en el key S3
        tmp_base = Path(tempfile.gettempdir())
        # Extraer nombre del archivo del key S3
        _, key = _parse_s3_path(original_input)
        filename = key.split('/')[-1] if '/' in key else key
        tmp_file = tmp_base / f"s3_download_{filename}"
        return _download_from_s3(original_input, tmp_file)

    # Comportamiento original para paths locales
    video_src = Path(original_input)
    upload_dir = os.getenv('UPLOAD_DIR', '/app/storage/uploads')
    if str(video_src).startswith(MNT_UPLOADS_PREFIX):
        rel = str(video_src)[len(MNT_UPLOADS_PREFIX):].lstrip('/')
        return Path(upload_dir) / rel
    return video_src


def _collect_inputs(video_src, intro_path, outro_path, watermark_path):
    """Collect ffmpeg input paths and return (inputs, intro_present, outro_present, wm_input_index).

    This isolates the simple task of appending inputs and avoids branching inside
    the larger gather function.
    """
    inputs = []
    inp_index = 0

    def add_input(path):
        nonlocal inp_index
        inputs.append(str(path))
        inp_index += 1

    intro_present = False
    if intro_path and Path(intro_path).exists():
        add_input(intro_path)
        intro_present = True

    # main input
    add_input(video_src)

    outro_present = False
    if outro_path and Path(outro_path).exists():
        add_input(outro_path)
        outro_present = True

    wm_input_index = None
    if watermark_path and Path(watermark_path).exists():
        wm_input_index = inp_index
        add_input(watermark_path)

    return inputs, intro_present, outro_present, wm_input_index


def _compute_indices(intro_present, outro_present, wm_input_index):
    """Compute numeric indices for intro/main/outro/wm based on presence flags."""
    cur = 0
    idx_intro = cur if intro_present else None
    if intro_present:
        cur += 1
    idx_main = cur
    cur += 1
    idx_outro = cur if outro_present else None
    if outro_present:
        cur += 1
    idx_wm = wm_input_index if wm_input_index is not None else None
    return idx_intro, idx_main, idx_outro, idx_wm


def _build_overlay_labels(idx_intro, idx_outro, idx_wm):
    """Return overlay label names depending on whether watermark is present."""
    overlay_labels = []
    if idx_wm is not None:
        if idx_intro is not None:
            overlay_labels.append('intro_w')
        overlay_labels.append('main_w')
        if idx_outro is not None:
            overlay_labels.append('outro_w')
    else:
        if idx_intro is not None:
            overlay_labels.append('intro_s')
        overlay_labels.append('main_s')
        if idx_outro is not None:
            overlay_labels.append('outro_s')
    return overlay_labels


def _scaled_label(src_idx, name, trim_main=False):
    """Return the ffmpeg scale/trim filter label for a given src index and name."""
    if trim_main:
        return (
            f'[{src_idx}:v]trim=0:30,setpts=PTS-STARTPTS,'
            'scale=1280:720:force_original_aspect_ratio=decrease,'
            'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1'
            f'[{name}_s]'
        )
    return (
        f'[{src_idx}:v]scale=1280:720:force_original_aspect_ratio=decrease,'
        'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1'
        f'[{name}_s]'
    )


def _build_overlay_filters(idx_intro, idx_outro, idx_wm):
    """Return list of overlay filter strings when watermark index is provided."""
    parts = []
    if idx_wm is None:
        return parts
    seg_names = []
    if idx_intro is not None:
        seg_names.append('intro')
    seg_names.append('main')
    if idx_outro is not None:
        seg_names.append('outro')
    for name in seg_names:
        parts.append(f'[{name}_s][{idx_wm}:v]overlay=main_w-overlay_w-10:10[{name}_w]')
    return parts


def _gather_inputs(video_src, intro_path, outro_path, watermark_path):
    """Return a tuple (inputs, idx_intro, idx_main, idx_outro, idx_wm, overlay_labels).

    This function now delegates to smaller helpers for clarity and lower cognitive complexity.
    """
    inputs, intro_present, outro_present, wm_input_index = _collect_inputs(video_src, intro_path, outro_path, watermark_path)
    idx_intro, idx_main, idx_outro, idx_wm = _compute_indices(intro_present, outro_present, wm_input_index)
    overlay_labels = _build_overlay_labels(idx_intro, idx_outro, idx_wm)
    return inputs, idx_intro, idx_main, idx_outro, idx_wm, overlay_labels


def _build_filter_and_cmd(inputs, idx_intro, idx_main, idx_outro, idx_wm, overlay_labels, tmpdir):
    """Return (cmd, out_file) prepared for subprocess.run.

    Delegate construction of sub-parts to smaller helpers to keep complexity low.
    """
    fc_parts = []
    if idx_intro is not None:
        fc_parts.append(_scaled_label(idx_intro, 'intro'))
    fc_parts.append(_scaled_label(idx_main, 'main', trim_main=True))
    if idx_outro is not None:
        fc_parts.append(_scaled_label(idx_outro, 'outro'))

    # overlay filters when watermark present
    fc_parts.extend(_build_overlay_filters(idx_intro, idx_outro, idx_wm))

    n_segments = len(overlay_labels)
    if n_segments == 1:
        concat_part = ''
    else:
        inputs_for_concat = ''.join(f'[{lbl}]' for lbl in overlay_labels)
        concat_part = f'{inputs_for_concat}concat=n={n_segments}:v=1:a=0[v]'

    filter_complex = ';'.join(fc_parts + ([concat_part] if concat_part else []))

    # Build ffmpeg command
    cmd = ['ffmpeg', '-y']
    for p in inputs:
        cmd.extend(['-i', p])

    cmd.extend(['-filter_complex', filter_complex])

    if n_segments == 1:
        cmd.extend(['-map', f'[{overlay_labels[0]}]'])
    else:
        cmd.extend(['-map', '[v]'])

    out_file = tmpdir / 'output.mp4'
    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-an',
        str(out_file)
    ])

    return cmd, out_file


def _compute_output_path(original_input, processed_dir, video_src):
    """Compute output path (string). If input is S3, return an S3 URL string.

    For local inputs return a filesystem path string under `processed_dir`.
    """
    input_str = str(original_input)

    # Si input era S3, output también debe ser S3 (retornamos string)
    if _is_s3_path(input_str):
        bucket, key = _parse_s3_path(input_str)
        if key.startswith('uploads/'):
            processed_key = key.replace('uploads/', 'processed/', 1)
        else:
            processed_key = f'processed/{key}'
        return f"s3://{bucket}/{processed_key}"

    # Local: construir path bajo processed_dir y devolver como string
    if input_str.startswith(MNT_UPLOADS_PREFIX):
        rel = input_str[len(MNT_UPLOADS_PREFIX):]
        rel = rel.lstrip('/')
        return (Path(processed_dir) / rel).as_posix()
    return (Path(processed_dir) / video_src.name).as_posix()


def _ensure_parent_dir(path: str | Path):
    """Try to create parent directory, but accept str or Path.

    - If `path` is an S3 URL (starts with 's3://') do nothing.
    - If `path` is a string, convert to `Path` before using `.parent`.
    - Handle PermissionError (CI) by warning instead of raising.
    """
    parent = None
    try:
        # If caller passed a string, handle S3 or convert to Path
        if isinstance(path, str):
            if _is_s3_path(path):
                # S3 outputs don't have local parent directories
                return
            path = Path(path)

        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # parent may be None if conversion failed; use a safe string for the message
        parent_display = str(parent) if parent is not None else str(path)
        logger.warning(
            'No permission to create processed directory %s; continuing (CI/test environment?)',
            parent_display,
        )
    except Exception as e:
        parent_display = str(parent) if parent is not None else str(path)
        logger.error('Failed creating processed directory %s: %s', parent_display, e)
        raise


def _update_db_if_needed(video_id, correlation_id, output_str, db_url):
    """Update DB if video_id and db_url are provided; convert async dsn if needed."""
    if not (video_id and db_url):
        return
    if db_url.startswith('postgresql+asyncpg://'):
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://', 1)

    logger.info(
        'Updating DB for video id=%s correlation_id=%s processed_path=%s',
        video_id,
        correlation_id,
        output_str,
    )
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE videos SET status=%s, processed_path=%s, processed_at=now(), correlation_id=%s WHERE id=%s",
                ('processed', output_str, correlation_id, str(video_id))
            )
            if cur.rowcount == 0:
                logger.warning('No rows updated for video id=%s', video_id)


@shared_task(bind=True, name="tasks.process_video.run")
def run(self, *args, **kwargs):
    """Process a video file:

    Steps:
    - Trim main video to max 30s
    - Scale/pad to 1280x720 (16:9)
    - Remove audio
    - Overlay watermark
    - Concatenate intro + main + outro (if intro/outro present)

    The task reads asset paths from env vars:
      ANB_INTRO_PATH, ANB_OUTRO_PATH, ANB_WATERMARK_PATH

    The implementation uses ffmpeg called via subprocess.
    """

    # Normalize possible test-provided task-like first arg
    task_self, args = _extract_task_self_and_args(self, args)

    # Parse logical task arguments
    video_id, input_path, correlation_id = _parse_task_args(args, kwargs)

    logger.info(
        'Starting video processing task video_id=%s correlation_id=%s input_path=%s args=%s kwargs=%s',
        video_id,
        correlation_id,
        input_path,
        args,
        kwargs,
    )
    tracer = trace.get_tracer("anb-worker.tasks")

    if not input_path:
        raise ValueError('process_video.run requires input_path as first or second positional argument')

    # Validación estricta: requerimos DB_URL_CORE en el entorno (RDS)
    db_url_env = os.environ.get('DB_URL_CORE')
    if not db_url_env:
        # Fallar temprano si falta configuración crítica
        raise RuntimeError('DB_URL_CORE no está definido en el entorno y es obligatorio para actualizar el estado en RDS')

    # Keep original incoming path (from API message) for later mirroring
    original_input = input_path
    video_src = _resolve_worker_path(original_input)

    # Log which path we'll use inside the worker for debugging
    logger.info(
        'Input original path=%s ; worker-resolved path=%s ; video_id=%s ; correlation_id=%s',
        original_input,
        video_src,
        video_id,
        correlation_id,
    )
    if not video_src.exists():
        logger.error('Input video not found: %s (resolved=%s)', original_input, video_src)
        raise task_self.retry(exc=FileNotFoundError(f'Input not found: {original_input}'), countdown=10, max_retries=2)

    # intro and outro are the same asset (INOUT)
    # If env vars are not provided, default to the assets folder inside the worker container
    inout_path = os.getenv('ANB_INOUT_PATH', '/app/assets/inout.mp4')
    intro_path = inout_path
    outro_path = inout_path
    watermark_path = os.getenv('ANB_WATERMARK_PATH', '/app/assets/watermark.png')

    logger.info('Using assets: inout=%s watermark=%s', inout_path, watermark_path)

    tmpdir = Path(tempfile.mkdtemp(prefix='proc_'))
    logger.info(
        'Processing video %s (video_id=%s correlation_id=%s) in tmpdir %s',
        input_path,
        video_id,
        correlation_id,
        tmpdir,
    )

    try:
        with tracer.start_as_current_span("tasks.process_video", attributes={
            "video.id": str(video_id),
            "task.correlation_id": str(correlation_id),
            "input.path": str(input_path),
        }):
            # Gather inputs and determine stream indices
            inputs, idx_intro, idx_main, idx_outro, idx_wm, overlay_labels = _gather_inputs(
                video_src, intro_path, outro_path, watermark_path
            )

            # Build ffmpeg command and filter_complex
            cmd, out_file = _build_filter_and_cmd(inputs, idx_intro, idx_main, idx_outro, idx_wm, overlay_labels, tmpdir)

            # Run and capture output
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                logger.error('ffmpeg failed: %s', proc.stderr.decode('utf-8', errors='ignore'))
                raise task_self.retry(exc=RuntimeError('ffmpeg failed'), countdown=30, max_retries=2)

            # At this point, out_file should exist
            if not out_file.exists():
                logger.error('Expected output not found at %s', out_file)
                raise task_self.retry(exc=RuntimeError('output missing'), countdown=10, max_retries=2)

            # Compute final processed path by mirroring uploads -> processed
            # Use PROCESSED_DIR (shared storage with API) as base for processed files.
            processed_dir = os.getenv('PROCESSED_DIR', '/app/storage/processed')
            output_path = _compute_output_path(original_input, processed_dir, video_src)

            # Make sure the parent directory exists. In some CI environments (e.g. when
            # PROCESSED_DIR is like '/processed') the process may not have permission
            # to create the directory. In that case we log a warning and continue; the
            # move operation is often mocked in tests so we should not fail the task
            # on PermissionError here.
            _ensure_parent_dir(output_path)

            # Determinar si el output es S3 o local
            is_s3_output = _is_s3_path(output_path)

            if is_s3_output:
                # Output es S3: enviar la ruta tal cual (string) a la función de upload
                output_str = output_path
                try:
                    _upload_to_s3(out_file, output_str)
                    logger.info('Subido archivo procesado a S3: %s', output_str)
                    # Limpiar archivo local después de subir
                    try:
                        out_file.unlink()
                    except Exception as e:
                        logger.warning('No se pudo eliminar archivo temporal %s: %s', out_file, e)
                except Exception as e:
                    logger.error('Failed to upload output to S3: %s', e)
                    raise task_self.retry(exc=e, countdown=10, max_retries=2)
            else:
                # Output es local: output_path es ya un string de filesystem
                output_str = output_path
                try:
                    shutil.move(str(out_file), output_str)
                    logger.info('Moved processed file to %s', output_str)
                except Exception as e:
                    logger.error('Failed to move output to final location: %s', e)
                    raise task_self.retry(exc=e, countdown=10, max_retries=2)

            # Update database record for the video if video_id is available (direct DB update)
            _update_db_if_needed(video_id, correlation_id, output_str, db_url_env)

            # Return the final path so caller (API) can register it
            return {"status": "ok", "output": output_str}

    except Exception as exc:
        # Record in current span if present
        try:
            span = trace.get_current_span()
            span.record_exception(exc)
            span.set_attribute("error", True)
        except Exception:
            pass
        logger.exception('Processing failed')
        raise task_self.retry(exc=exc, countdown=30, max_retries=2)
    finally:
        # cleanup: remove temp files
        # Si descargamos desde S3, también limpiar ese archivo
        try:
            if _is_s3_path(original_input):
                # Buscar y limpiar archivo descargado de S3 si existe
                _, key = _parse_s3_path(original_input)
                filename = key.split('/')[-1] if '/' in key else key
                s3_download_path = Path(tempfile.gettempdir()) / f"s3_download_{filename}"
                if s3_download_path.exists():
                    try:
                        s3_download_path.unlink()
                        logger.debug('Eliminado archivo temporal descargado de S3: %s', s3_download_path)
                    except Exception as e:
                        logger.warning('No se pudo eliminar archivo descargado de S3 %s: %s', s3_download_path, e)
        except Exception:
            pass

        # Limpiar tmpdir
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass


def _raise_retry(task_self, exc, countdown=10, max_retries=2):
    """Helper to raise task retry in a single line to keep run() concise."""
    raise task_self.retry(exc=exc, countdown=countdown, max_retries=max_retries)
