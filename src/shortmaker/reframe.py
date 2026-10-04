"""CPU anime detection and bounded crop trajectories; no identity or landmarks."""
import json
import logging
import math
from pathlib import Path
from .paths import ROOT
from .ffmpeg_runner import Cancelled

CASCADE = ROOT / "models/anime/lbpcascade_animeface.xml"
SAMPLE_FPS = 2


def clamp(value, low=0, high=1):
    return max(low, min(high, value))


def focus_faces(faces, previous, frame_width, frame_height, zoom=1):
    """Largest face unless previous focus has a similarly large nearby candidate."""
    if not faces:
        return None
    ordered = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    selected = ordered[0]
    if previous is not None:
        nearby = min(ordered, key=lambda f: math.hypot((f[0]+f[2]/2)/frame_width-previous[0], (f[1]+f[3]/2)/frame_height-previous[1]))
        distance = math.hypot((nearby[0]+nearby[2]/2)/frame_width-previous[0], (nearby[1]+nearby[3]/2)/frame_height-previous[1])
        if nearby[2]*nearby[3] >= selected[2]*selected[3]*.65 and distance < .25:
            selected = nearby
    x, y, w, h = selected
    # Try a second similarly relevant face only if their union fits the central 80%.
    scale = max(1080/frame_width, 1920/frame_height)*zoom
    crop_w, crop_h = 1080/scale, 1920/scale
    box = (x, y, x+w, y+h)
    for other in ordered:
        if other == selected or other[2]*other[3] < w*h*.5:
            continue
        ox, oy, ow, oh = other
        union = (min(x, ox), min(y, oy), max(x+w, ox+ow), max(y+h, oy+oh))
        if union[2]-union[0] <= crop_w*.8 and union[3]-union[1] <= crop_h*.8:
            box = union
            break
    return ((box[0]+box[2])/2/frame_width, (box[1]+box[3])/2/frame_height)


def smooth_focus(target, previous, crop_width_fraction, alpha=.55):
    if previous is None:
        return target
    x = previous[0] + alpha*(target[0]-previous[0])
    y = previous[1] + alpha*(target[1]-previous[1])
    # Don't let smoothing leave the chosen face outside the central safe area.
    max_lag = crop_width_fraction*.25
    return (clamp(x, target[0]-max_lag, target[0]+max_lag), clamp(y, target[1]-.2, target[1]+.2))


def trajectory_expression(points, axis):
    """Smoothstep interpolation; hold endpoints; FFmpeg evaluates t per video frame."""
    expression = f"{points[0][axis]:.8f}"
    for a, b in zip(points, points[1:]):
        dt = b[0]-a[0]
        u = f"clip((t-{a[0]:.6f})/{dt:.6f},0,1)"
        if abs(b[axis]-a[axis]) > 1e-8:
            expression += f"+({b[axis]-a[axis]:.8f})*({u})*({u})*(3-2*({u}))"
    return expression


def crop_filter(points):
    x = trajectory_expression(points, 1)
    y = trajectory_expression(points, 2)
    return f"crop=1080:1920:x='max(0,min(iw-1080,iw*({x})-540))':y='max(0,min(ih-1920,ih*({y})-960))'"


def analyze_anime(source, segment, temp, index, runner, ffmpeg):
    stats = {"requested_mode": "anime_face_track", "effective_mode": "center_crop", "sample_fps": SAMPLE_FPS,
             "sampled_frames": 0, "frames_with_faces": 0, "detection_rate": 0, "fallback": True, "fallback_samples": 0}
    points = []
    try:
        import cv2
        if not CASCADE.is_file():
            raise ValueError("cascade de anime não instalado")
        detector = cv2.CascadeClassifier(str(CASCADE))
        if detector.empty():
            raise ValueError("cascade de anime inválido")
        folder = Path(temp) / f"anime-{index}"
        folder.mkdir()
        runner.run([ffmpeg, "-y", "-v", "error", "-ss", segment.start, "-t", segment.end-segment.start,
                    "-i", source, "-an", "-vf", f"fps={SAMPLE_FPS},scale=960:-2", "-q:v", 2, folder / "sample-%05d.jpg"])
        samples = []
        for i, path in enumerate(sorted(folder.glob("sample-*.jpg"))):
            runner.check()
            image = cv2.imread(str(path))
            if image is None:
                continue
            height, width = image.shape[:2]
            gray = cv2.equalizeHist(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
            faces = [tuple(int(v) for v in f) for f in detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))]
            at = i/SAMPLE_FPS/segment.speed
            samples.append((at, width, height, faces))
        previous = None
        last_detection = None
        stats["raw_frames_with_faces"] = sum(bool(sample[3]) for sample in samples)
        for i, (at, width, height, raw_faces) in enumerate(samples):
            runner.check()
            # Reject isolated positives: require a nearby face on an adjacent sample.
            neighbors = [f for j in (i-1, i+1) if 0 <= j < len(samples) for f in samples[j][3]]
            faces = [f for f in raw_faces if any(math.hypot((f[0]+f[2]/2)-(n[0]+n[2]/2), (f[1]+f[3]/2)-(n[1]+n[3]/2)) < max(f[2], n[2])*1.5 for n in neighbors)]
            stats["sampled_frames"] += 1
            target = focus_faces(faces, previous, width, height, segment.reframe.zoom)
            if target is not None:
                stats["frames_with_faces"] += 1
                last_detection = at
                crop_fraction = min(1, (height*9/16)/width/segment.reframe.zoom)
                target = smooth_focus(target, previous, crop_fraction)
            elif previous is not None and last_detection is not None and at-last_detection <= .75/segment.speed:
                target = previous  # tolerate one missed sample without shaking
            else:
                target = (.5, .5)
                stats["fallback_samples"] += 1
            points.append((at, clamp(target[0]), clamp(target[1])))
            previous = target
        if stats["sampled_frames"]:
            stats["detection_rate"] = stats["frames_with_faces"]/stats["sampled_frames"]
        if stats["frames_with_faces"] >= 2:
            stats["effective_mode"] = "anime_face_track"
            stats["fallback"] = stats["fallback_samples"] > 0
        else:
            points = [(0, .5, .5)]
            stats["fallback_reason"] = "sem detecção confiável (mínimo 2 amostras com rosto)"
    except Cancelled:
        raise
    except Exception as exc:
        logging.warning("Anime tracking: fallback center_crop: %s", exc)
        points = [(0, .5, .5)]
        stats["fallback_reason"] = str(exc)
    stats["keyframes"] = [{"at": t, "x": x, "y": y} for t, x, y in points]
    logging.info("Anime tracking: %s", json.dumps(stats, ensure_ascii=False))
    return points, stats
