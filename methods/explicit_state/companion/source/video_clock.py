"""Original qualified encoder with packet metadata and one explicit full decode.

No scientific reader, interpolation or model calls. Runtime equality, not the
documentation alone, establishes clock/count/dimension acceptance.
"""
import hashlib
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path


def manifest_pts(timestamps):
    values = [int(v) for v in timestamps]
    if len(values) < 2 or any(b <= a for a, b in zip(values, values[1:])):
        raise ValueError('Strict integer native timestamps required')
    origin = values[0]
    pts = [(v-origin+500)//1000 for v in values]
    if any(b <= a for a, b in zip(pts, pts[1:])):
        raise ValueError('Distinct samples collapse at microsecond encoding resolution')
    return pts


def verify_packet_metadata(value, pts, dimensions):
    stream, = value['streams']
    packets = value['packets']
    durations = [b-a for a, b in zip(pts, pts[1:])] + [1]
    if (stream['time_base'] != '1/1000000' or len(packets) != len(pts) or
            [int(p['pts']) for p in packets] != pts or
            [int(p['dts']) for p in packets] != pts or
            [int(p['duration']) for p in packets] != durations or
            int(stream['duration_ts']) != pts[-1]+1 or
            (stream['width'], stream['height']) != tuple(dimensions)):
        raise ValueError('Packet native-PTS/count/duration/size acceptance failed')
    return stream


def verify_single_decode(text, pts, dimensions):
    """Strict raw-frame MD5 output parser; does not itself decode anything."""
    tb = re.findall(r'^#tb\s+0:\s*(\d+/\d+)\s*$', text, re.M)
    size = re.findall(r'^#dimensions\s+0:\s*(\d+)x(\d+)\s*$', text, re.M)
    codec = re.findall(r'^#codec_id\s+0:\s*(\S+)\s*$', text, re.M)
    if tb != ['1/1000000'] or size != [(str(dimensions[0]), str(dimensions[1]))] or codec != ['rawvideo']:
        raise ValueError('Decoded-frame header acceptance failed')
    rows = [line for line in text.splitlines() if line and not line.startswith('#')]
    if len(rows) != len(pts):
        raise ValueError('Full media decode missed or duplicated a saved sample')
    expected_size = dimensions[0]*dimensions[1]*3//2
    for expected, line in zip(pts, rows):
        fields = [s.strip() for s in line.split(',')]
        if (len(fields) != 6 or int(fields[0]) != 0 or int(fields[2]) != expected or
                int(fields[4]) != expected_size or not re.fullmatch(r'[0-9a-fA-F]{32}', fields[5])):
            raise ValueError('Decoded-frame PTS/size/checksum acceptance failed')
    return dict(decoded_frames=len(rows), full_frame_decode_passes=1,
                decoded_time_base=str(Fraction(tb[0])), dimensions=list(dimensions))


def encode(ffmpeg, ffprobe, frames, timestamps, output, dimensions):
    pts = manifest_pts(timestamps)
    if len(pts) != len(frames):
        raise ValueError('Clock/frame count mismatch')
    output = Path(output)
    concat = output.with_suffix('.ffconcat')
    if output.exists() or concat.exists():
        raise RuntimeError('Independent output already exists; no retry')
    lines = ['ffconcat version 1.0']
    for i, path in enumerate(frames):
        path = Path(path)
        if "'" in str(path) or '\n' in str(path):
            raise ValueError('Unsupported manifest path')
        lines += ["file '%s'" % path.as_posix(), 'option framerate 1000000',
                  'duration %.6f' % ((pts[i+1]-pts[i] if i+1<len(pts) else 1)/1e6)]
    with concat.open('x', encoding='utf8') as stream:
        stream.write('\n'.join(lines)+'\n')
    command = [ffmpeg, '-hide_banner', '-loglevel', 'warning', '-nostdin', '-n',
               '-f', 'concat', '-safe', '0', '-i', str(concat), '-an',
               '-fps_mode', 'passthrough', '-c:v', 'libx264', '-preset', 'medium',
               '-crf', '18', '-bf', '0', '-pix_fmt', 'yuv420p', '-threads', '1',
               '-enc_time_base', '1:1000000', '-video_track_timescale', '1000000',
               '-movflags', '+faststart', str(output)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        raise RuntimeError('VFR encoder failed: '+completed.stderr[-4000:])
    query = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'v:0',
                            '-show_streams', '-show_packets', '-of', 'json', str(output)],
                           capture_output=True, text=True, check=True)
    stream = verify_packet_metadata(json.loads(query.stdout), pts, dimensions)
    # No -show_frames pass. Packet probing is not claimed to perform zero
    # internal decoder work; only this next explicit full decode is counted.
    check = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin',
                            '-threads', '1', '-copyts', '-i', str(output),
                            '-map', '0:v:0', '-an', '-fps_mode', 'passthrough',
                            '-c:v', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-enc_time_base', '1:1000000', '-f', 'framemd5', '-'],
                           capture_output=True, text=True, check=True)
    decoded = verify_single_decode(check.stdout, pts, dimensions)
    return dict(path=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                bytes=output.stat().st_size, pts_us=pts, time_base=stream['time_base'],
                **decoded,
                max_timestamp_rounding_error_ns=max(abs((int(t)-int(timestamps[0]))-p*1000)
                                                     for t,p in zip(timestamps,pts)),
                full_frame_decode_verified=True, encoder_stderr=completed.stderr[-4000:],
                final_packet_duration_us=1, stream_duration_us=int(stream['duration_ts']),
                packet_probe_internal_decoder_visits_not_assumed_zero=True,
                interpolation=False, outside_sample_span='UNKNOWN; not presented',
                holds_between_samples='Visual persistence only, not intermediate state estimates')
