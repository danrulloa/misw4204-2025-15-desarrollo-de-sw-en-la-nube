from celery import shared_task
import subprocess
import tempfile
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="tasks.process_video.run")
def run(self, input_path: str):
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
    # Keep original incoming path (from API message) for later mirroring
    original_input = input_path
    video_src = Path(input_path)
    # Map API container absolute upload path (/mnt/uploads/...) to worker local UPLOAD_DIR
    upload_dir = os.getenv('UPLOAD_DIR', '/app/storage/uploads')
    if str(video_src).startswith('/mnt/uploads'):
        rel = str(video_src)[len('/mnt/uploads'):].lstrip('/')
        video_src = Path(upload_dir) / rel

    # Log which path we'll use inside the worker for debugging
    logger.info('Input original path=%s ; worker-resolved path=%s', original_input, video_src)
    if not video_src.exists():
        logger.error('Input video not found: %s (resolved=%s)', original_input, video_src)
        raise self.retry(exc=FileNotFoundError(f'Input not found: {original_input}'), countdown=10, max_retries=2)

    # intro and outro are the same asset (INOUT)
    # If env vars are not provided, default to the assets folder inside the worker container
    inout_path = os.getenv('ANB_INOUT_PATH', '/app/assets/inout.mp4')
    intro_path = inout_path
    outro_path = inout_path
    watermark_path = os.getenv('ANB_WATERMARK_PATH', '/app/assets/watermark.png')

    logger.info('Using assets: inout=%s watermark=%s', inout_path, watermark_path)

    tmpdir = Path(tempfile.mkdtemp(prefix='proc_'))
    logger.info('Processing video %s in tmpdir %s', input_path, tmpdir)

    try:
        # Prepare list of inputs and build filter_complex dynamically
        inputs = []
        filter_parts = []
        stream_labels = []

        inp_index = 0
        # helper to add a video input
        def add_input(path):
            nonlocal inp_index
            inputs.append(str(path))
            label = f'v{inp_index}'
            inp_index += 1
            return label

        # Add intro if present
        intro_label = None
        if intro_path and Path(intro_path).exists():
            add_input(intro_path)
            intro_label = 'intro'
        # main input
        add_input(video_src)
        main_label = 'main'
        # outro if present
        outro_label = None
        if outro_path and Path(outro_path).exists():
            add_input(outro_path)
            outro_label = 'outro'

        # watermark (optional) - add as last input if provided
        wm_input_index = None
        if watermark_path and Path(watermark_path).exists():
            wm_input_index = inp_index
            add_input(watermark_path)

        # Build filter chains: for each video input we will scale/pad to 1280x720
        # and remove audio. Trim is applied only to the main input.
        in_idx = 0
        labels_after_scale = []
        total_video_inputs = inp_index
        # Determine which indices correspond to intro/main/outro/wm
        # Order of inputs in ffmpeg: intro?(0) main(?), outro?(?), watermark?(last if present)
        # We'll compute based on presence
        cur = 0
        if intro_label:
            # intro is at cur
            idx_intro = cur
            cur += 1
        else:
            idx_intro = None
        idx_main = cur
        cur += 1
        if outro_label:
            idx_outro = cur
            cur += 1
        else:
            idx_outro = None
        if wm_input_index is not None:
            idx_wm = wm_input_index
        else:
            idx_wm = None

        # For each of intro/main/outro create scaled stream labels
        def scaled_label(src_idx, name, trim_main=False):
            # src_idx is the input file index
            # name is label base
            if trim_main:
                # trim to 30s
                return (
                    f'[{src_idx}:v]trim=0:30,setpts=PTS-STARTPTS,'
                    'scale=1280:720:force_original_aspect_ratio=decrease,'
                    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1'
                    f'[{name}_s]'
                )
            else:
                return (
                    f'[{src_idx}:v]scale=1280:720:force_original_aspect_ratio=decrease,'
                    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1'
                    f'[{name}_s]'
                )

        fc_parts = []
        if idx_intro is not None:
            fc_parts.append(scaled_label(idx_intro, 'intro'))
        fc_parts.append(scaled_label(idx_main, 'main', trim_main=True))
        if idx_outro is not None:
            fc_parts.append(scaled_label(idx_outro, 'outro'))

        # Overlay watermark on each segment if watermark exists
        overlay_labels = []
        if idx_wm is not None:
            # watermark input index is idx_wm
            segs = []
            seg_names = []
            if idx_intro is not None:
                segs.append(('intro', idx_intro))
                seg_names.append('intro')
            segs.append(('main', idx_main))
            seg_names.append('main')
            if idx_outro is not None:
                segs.append(('outro', idx_outro))
                seg_names.append('outro')

            for name in seg_names:
                # overlay: [name_s][wm]overlay=... -> [name_w]
                fc_parts.append(f'[{name}_s][{idx_wm}:v]overlay=main_w-overlay_w-10:10[{name}_w]')
                overlay_labels.append(f'{name}_w')
        else:
            # No watermark, just use scaled labels
            if idx_intro is not None:
                overlay_labels.append('intro_s')
            overlay_labels.append('main_s')
            if idx_outro is not None:
                overlay_labels.append('outro_s')

        # Build concat part
        n_segments = len(overlay_labels)
        if n_segments == 1:
            # only main
            final_map = f'[{overlay_labels[0]}]'
            # map directly without concat
            concat_part = ''
        else:
            # create concat filter
            # join labels
            inputs_for_concat = ''.join(f'[{lbl}]' for lbl in overlay_labels)
            concat_part = f'{inputs_for_concat}concat=n={n_segments}:v=1:a=0[v]'

        # Assemble filter_complex
        filter_complex = ';'.join(fc_parts + ([concat_part] if concat_part else []))

        # Build ffmpeg command
        cmd = ['ffmpeg', '-y']
        for p in inputs:
            cmd.extend(['-i', p])

        cmd.extend(['-filter_complex', filter_complex])

        if n_segments == 1:
            # map the single label
            if idx_wm is not None:
                out_map = f'-map [{overlay_labels[0]}]'
            else:
                out_map = f'-map [{overlay_labels[0]}]'
            # will add as tokens
            cmd.extend(['-map', f'[{overlay_labels[0]}]'])
        else:
            cmd.extend(['-map', '[v]'])

        # output settings
        out_file = tmpdir / 'output.mp4'
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-an',
            str(out_file)
        ])

        logger.info('Running ffmpeg command: %s', ' '.join(cmd))
        # Run and capture output
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            logger.error('ffmpeg failed: %s', proc.stderr.decode('utf-8', errors='ignore'))
            raise self.retry(exc=RuntimeError('ffmpeg failed'), countdown=30, max_retries=2)

        # At this point, out_file should exist
        if not out_file.exists():
            logger.error('Expected output not found at %s', out_file)
            raise self.retry(exc=RuntimeError('output missing'), countdown=10, max_retries=2)

        # Compute final processed path by mirroring uploads -> processed
        # Use PROCESSED_DIR (shared storage with API) as base for processed files.
        processed_dir = os.getenv('PROCESSED_DIR', '/app/storage/processed')
        # Use the original incoming path (from API) to preserve same relative location
        input_str = str(original_input)
        if input_str.startswith('/mnt/uploads'):
            # preserve subpath after /mnt/uploads
            rel = input_str[len('/mnt/uploads'):]
            rel = rel.lstrip('/')
            output_path = Path(processed_dir) / rel
        else:
            # fallback to PROCESSED_DIR/<basename>
            output_path = Path(processed_dir) / video_src.name

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Move final file into the processed storage location
        try:
            shutil.move(str(out_file), str(output_path))
            logger.info('Moved processed file to %s', output_path)
        except Exception as e:
            logger.error('Failed to move output to final location: %s', e)
            raise self.retry(exc=e, countdown=10, max_retries=2)

        # Return the final path so caller (API) can register it
        return {"status": "ok", "output": str(output_path)}

    except Exception as exc:
        logger.exception('Processing failed')
        raise self.retry(exc=exc, countdown=30, max_retries=2)
    finally:
        # cleanup: keep output for caller; remove temp files except output? We'll keep tmpdir for debugging if needed.
        # For now, remove temp dir to avoid disk leak
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
