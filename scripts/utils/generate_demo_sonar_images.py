"""
generate_demo_sonar_images.py
─────────────────────────────
Generates realistic side-scan sonar waterfall images for the TARANG-DEMO-001
detections that have no evidence imagery, saves them to outputs/, and
persists the correct sonar_image + evidence_detection_link dispatch events
so the Survey Portal shows real images immediately — no placeholders.

Run once: python generate_demo_sonar_images.py
Safe to re-run: skips detections that already have a linked image.
"""
import sys, os, uuid, hashlib, json, io, logging
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
log = logging.getLogger('sonar_gen')

# ── deps ──────────────────────────────────────────────────────────────────────
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import requests as req

# ── config ────────────────────────────────────────────────────────────────────
DEMO_SURVEY_ID = '6d17c69e-6d2c-5e13-8584-627bc50e9453'
OUTPUTS_DIR    = os.path.join(os.path.dirname(__file__), 'outputs', 'sonar_evidence')
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Import local supabase_service (same process-level config as app.py)
sys.path.insert(0, os.path.dirname(__file__))
import supabase_service as sb

# ── sonar image generator ─────────────────────────────────────────────────────
CLASS_SIGNATURES = {
    'ghost_net':           dict(shape='diffuse',   brightness=0.55, texture='rough',  shadow_len=0.15),
    'shipwreck':           dict(shape='elongated', brightness=0.90, texture='hard',   shadow_len=0.35),
    'mine_cylinder':       dict(shape='compact',   brightness=0.95, texture='hard',   shadow_len=0.25),
    'submarine_pipeline':  dict(shape='linear',    brightness=0.85, texture='hard',   shadow_len=0.20),
    'crab_pot':            dict(shape='compact',   brightness=0.65, texture='medium', shadow_len=0.12),
    'unknown':             dict(shape='diffuse',   brightness=0.50, texture='rough',  shadow_len=0.10),
}
DEFAULT_SIG = dict(shape='compact', brightness=0.70, texture='medium', shadow_len=0.18)

def _perlin_noise(h, w, scale=8, rng=None):
    """Simple multi-octave noise used as sonar seafloor texture."""
    if rng is None:
        rng = np.random.default_rng()
    noise = np.zeros((h, w), dtype=np.float32)
    amplitude, frequency, persistence = 1.0, 1.0, 0.5
    for _ in range(4):
        sh = max(2, int(h * frequency / scale))
        sw = max(2, int(w * frequency / scale))
        layer = rng.random((sh, sw)).astype(np.float32)
        from PIL import Image as _I
        layer_img = _I.fromarray((layer * 255).astype(np.uint8)).resize((w, h), _I.BILINEAR)
        noise += amplitude * (np.array(layer_img, dtype=np.float32) / 255.0)
        amplitude *= persistence
        frequency *= 2.0
    noise /= noise.max() + 1e-8
    return noise


def generate_sonar_image(class_name, detection_id, confidence, width=512, height=256, seed=None):
    """
    Render a realistic grayscale side-scan sonar waterfall strip.

    Layout (left→right): nadir (black centre seam) | port backscatter |
    acoustic shadow | target highlight | starboard backscatter.
    The image is returned as JPEG bytes.
    """
    sig  = CLASS_SIGNATURES.get(class_name, DEFAULT_SIG)
    rng  = np.random.default_rng(seed if seed is not None else abs(hash(detection_id)) % (2**31))

    # ── 1. Seafloor texture ───────────────────────────────────────────────────
    noise = _perlin_noise(height, width, scale=12, rng=rng)
    # Low reflectivity baseline (sonar sediment return)
    base_brightness = 0.22 + rng.random() * 0.12
    canvas = (noise * 0.18 + base_brightness)   # 0→1 float

    # ── 2. Nadir (centre seam) ────────────────────────────────────────────────
    nadir_col = width // 2
    nadir_half = 4
    canvas[:, nadir_col - nadir_half : nadir_col + nadir_half] *= 0.05

    # ── 3. Target position & highlight ────────────────────────────────────────
    # Place target on starboard side (right half), 1/3–2/3 down the strip
    tx = int(nadir_col + width * 0.20 + rng.random() * width * 0.18)
    ty = int(height * 0.30 + rng.random() * height * 0.40)

    shape = sig['shape']
    brt   = sig['brightness']
    tx_radius_x = {'elongated': 55, 'linear': 70, 'diffuse': 30, 'compact': 18}.get(shape, 22)
    tx_radius_y = {'elongated': 14, 'linear':  5, 'diffuse': 22, 'compact': 16}.get(shape, 14)
    tx_radius_x = max(10, min(tx_radius_x, width // 4))
    tx_radius_y = max(6,  min(tx_radius_y, height // 6))

    # Draw highlight blob
    yy, xx = np.mgrid[0:height, 0:width]
    dist = ((xx - tx) / tx_radius_x) ** 2 + ((yy - ty) / tx_radius_y) ** 2
    target_mask = np.exp(-dist * 1.6).astype(np.float32)
    canvas = np.clip(canvas + target_mask * brt * 0.75, 0, 1)

    # ── 4. Acoustic shadow ────────────────────────────────────────────────────
    shadow_len = int(width * sig['shadow_len'])
    shadow_len = max(20, min(shadow_len, width // 3))
    sx1, sx2  = tx + tx_radius_x // 2, min(width - 1, tx + tx_radius_x // 2 + shadow_len)
    sy1, sy2  = max(0, ty - tx_radius_y), min(height, ty + tx_radius_y + 2)
    if sx2 > sx1 and sy2 > sy1:
        # Shadow fades from dark to seafloor level
        shadow_gradient = np.linspace(0.03, base_brightness, sx2 - sx1)
        canvas[sy1:sy2, sx1:sx2] = np.minimum(canvas[sy1:sy2, sx1:sx2],
                                               shadow_gradient[np.newaxis, :])

    # ── 5. Texture modulation ─────────────────────────────────────────────────
    texture_strength = {'hard': 0.03, 'medium': 0.06, 'rough': 0.10}.get(sig['texture'], 0.06)
    canvas += rng.standard_normal((height, width)).astype(np.float32) * texture_strength
    canvas  = np.clip(canvas, 0, 1)

    # ── 6. YOLO-style bounding box overlay ───────────────────────────────────
    pil_img = Image.fromarray((canvas * 255).astype(np.uint8), mode='L').convert('RGB')
    draw    = ImageDraw.Draw(pil_img)

    # Bounding box (pixel coords)
    bx1 = max(0, tx - tx_radius_x)
    by1 = max(0, ty - tx_radius_y)
    bx2 = min(width - 1,  tx + tx_radius_x)
    by2 = min(height - 1, ty + tx_radius_y)

    box_color = (0, 220, 180)   # teal — TARANG brand
    draw.rectangle([bx1, by1, bx2, by2], outline=box_color, width=2)

    # Label
    conf_pct = int(round(confidence if confidence <= 1.0 else confidence))
    label    = f'{class_name.replace("_"," ").title()} {conf_pct}%'
    draw.rectangle([bx1, by1 - 14, bx1 + len(label) * 6 + 4, by1], fill=(0, 0, 0))
    draw.text((bx1 + 2, by1 - 13), label, fill=box_color)

    # Detection ID watermark (bottom-left, tiny)
    draw.text((4, height - 12), detection_id[:22], fill=(80, 80, 80))

    # ── 7. Slight horizontal scan-line pattern (sonar realism) ───────────────
    arr = np.array(pil_img, dtype=np.float32)
    scanlines = np.ones(height, dtype=np.float32)
    scanlines[::2] *= 0.94
    arr *= scanlines[:, np.newaxis, np.newaxis]
    pil_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # ── 8. Return JPEG bytes ──────────────────────────────────────────────────
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG', quality=88, optimize=True)
    return buf.getvalue(), (bx1, by1, bx2 - bx1, by2 - by1)   # bytes, (x, y, w, h)


# ── main ──────────────────────────────────────────────────────────────────────
def run():
    # Get all detections for the demo survey
    dets = sb.get_all_detections(survey_id=DEMO_SURVEY_ID)
    if not dets:
        log.error('No detections found for demo survey %s', DEMO_SURVEY_ID)
        return

    # Get existing evidence links so we skip already-linked detections
    existing_links = sb.get_evidence_detection_links()
    existing_images = {str(img.get('image_id')): img for img in sb.get_sonar_images(DEMO_SURVEY_ID)}

    log.info('Demo survey: %s detections, %s existing images', len(dets), len(existing_images))

    survey_hash = hashlib.sha256(DEMO_SURVEY_ID.encode()).hexdigest()[:12]

    for seq_idx, det in enumerate(dets, start=1):
        det_id  = det.get('id') or ''
        cls_raw = det.get('class_name') or 'unknown'
        conf    = det.get('confidence') or 85.0
        title   = det.get('title') or cls_raw

        # Skip if already linked
        link = existing_links.get(str(det_id), {})
        if link.get('image_id') and str(link['image_id']) in existing_images:
            log.info('SKIP  %s — already has image %s', det_id, link['image_id'])
            continue

        log.info('GEN   %s  cls=%s  seq=%s', det_id, cls_raw, seq_idx)

        # Generate sonar image
        try:
            img_bytes, bbox_xywh = generate_sonar_image(
                class_name=cls_raw, detection_id=det_id, confidence=conf,
                seed=abs(hash(det_id)) % (2**31)
            )
        except Exception as exc:
            log.exception('Image generation failed for %s: %s', det_id, exc)
            continue

        # Stable image_id derived from survey + sequence (matches _persist_workflow_image logic)
        image_id  = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{DEMO_SURVEY_ID}:sonar:{seq_idx}'))
        filename  = f'sonar-{survey_hash}-seq{seq_idx:03d}.jpg'
        local_path = os.path.join(OUTPUTS_DIR, filename)
        local_url  = f'/outputs/sonar_evidence/{filename}'

        # Write to disk
        with open(local_path, 'wb') as fh:
            fh.write(img_bytes)
        log.info('SAVED %s  (%d bytes)', local_path, len(img_bytes))

        # Try to upload to Supabase Storage
        storage_path = f'evidence/{image_id}/sequence-{seq_idx:03d}.jpg'
        upload_result = sb.upload_sonar_image(storage_path, img_bytes, 'image/jpeg')
        public_url = upload_result.get('public_url') if upload_result else ''
        effective_url = public_url or local_url

        log.info('URL   %s  storage=%s', det_id, bool(public_url))

        # Persist sonar_image dispatch event
        sonar_event = {
            'survey_id':     DEMO_SURVEY_ID,
            'image_id':      image_id,
            'evidence_id':   image_id,
            'sequence':      seq_idx,
            'file_name':     filename,
            'file_hash':     hashlib.sha256(img_bytes).hexdigest(),
            'content_sha256': hashlib.sha256(img_bytes).hexdigest(),
            'content_type':  'image/jpeg',
            'storage_path':  storage_path,
            'storage_url':   public_url or '',
            'url':           effective_url,
            'local_url':     local_url,
            'local_path':    local_path,
            'ping_start':    (seq_idx - 1) * 500,
            'ping_end':      seq_idx * 500 - 1,
            'created_at':    datetime.now(timezone.utc).isoformat(),
        }
        ok_img = sb.log_dispatch_event('sonar_image', sonar_event)
        log.info('EVT sonar_image: ok=%s', ok_img)

        # Persist evidence_detection_link
        x, y, w, h = bbox_xywh
        link_event = {
            'detection_id': det_id,
            'survey_id':    DEMO_SURVEY_ID,
            'image_id':     image_id,
            'evidence_id':  image_id,
            'sequence':     seq_idx,
            'linked_at':    datetime.now(timezone.utc).isoformat(),
            'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
        }
        ok_lnk = sb.log_dispatch_event('evidence_detection_link', link_event)
        log.info('EVT evidence_detection_link: ok=%s  det=%s → img=%s', ok_lnk, det_id, image_id)

    log.info('Done. Verify with: python final_check.py')


if __name__ == '__main__':
    run()
