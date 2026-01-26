#!/usr/bin/env python3
import sys
import wave
import contextlib
try:
    import audioop
    _HAS_AUDIOOP = True
except Exception:
    _HAS_AUDIOOP = False
import json
import math

CHUNK = 1024 * 64

def analyze_wav(path):
    with contextlib.closing(wave.open(path,'rb')) as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()  # bytes
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        duration = nframes / float(framerate)

        max_possible = (2 ** (8 * sampwidth - 1)) - 1

        total_chunks = 0
        max_seen = 0
        rms_acc = 0.0
        clipped_chunks = 0

        wf.rewind()
        import struct
        # helper to unpack samples when audioop is unavailable
        def analyze_chunk_manual(data, sampwidth, channels):
            fmt = None
            if sampwidth == 1:
                # 8-bit unsigned
                fmt = f"{len(data)}B"
            elif sampwidth == 2:
                fmt = f"{len(data)//2}h"
            elif sampwidth == 3:
                # 24-bit: unpack manually
                # convert to signed 32-bit values
                samples = []
                for i in range(0, len(data), 3):
                    b = data[i:i+3]
                    # little-endian
                    val = int.from_bytes(b + (b"\x00"), byteorder='little', signed=False)
                    if val & 0x800000:
                        val = val - (1 << 24)
                    samples.append(val)
                return samples
            else:
                # support 4 bytes
                fmt = f"{len(data)//4}i"

            if fmt is not None:
                try:
                    vals = list(struct.unpack('<' + fmt, data))
                except Exception:
                    vals = []
                # for 8-bit (unsigned) convert to signed centered at 128
                if sampwidth == 1:
                    vals = [v - 128 for v in vals]
                return vals

        while True:
            data = wf.readframes(CHUNK)
            if not data:
                break
            total_chunks += 1
            if _HAS_AUDIOOP:
                try:
                    rms = audioop.rms(data, sampwidth)
                except Exception:
                    rms = 0
                rms_acc += rms
                try:
                    m = audioop.max(data, sampwidth)
                except Exception:
                    m = 0
                if m > max_seen:
                    max_seen = m
                if m >= max_possible - 1:
                    clipped_chunks += 1
            else:
                samples = analyze_chunk_manual(data, sampwidth, channels)
                if not samples:
                    continue
                # if stereo, samples are interleaved; compute per-sample absolute
                abs_samples = [abs(s) for s in samples]
                if abs_samples:
                    chunk_max = max(abs_samples)
                    if chunk_max > max_seen:
                        max_seen = chunk_max
                    # RMS
                    sq = sum(s*s for s in samples)
                    rms = math.sqrt(sq / len(samples)) if len(samples) else 0
                    rms_acc += rms
                    if chunk_max >= max_possible - 1:
                        clipped_chunks += 1

        mean_rms = (rms_acc / total_chunks) if total_chunks else 0

        # Convert RMS to dBFS: 20 * log10(rms / max_possible)
        def dbfs(r):
            if r <= 0:
                return -999.0
            return 20.0 * math.log10(r / float(max_possible))

        result = {
            "channels": channels,
            "sample_width_bytes": sampwidth,
            "sample_rate": framerate,
            "nframes": nframes,
            "duration_seconds": round(duration, 3),
            "max_sample_value": max_seen,
            "max_dbfs": round(dbfs(max_seen), 2) if max_seen>0 else None,
            "mean_rms": round(mean_rms, 2),
            "mean_dbfs": round(dbfs(mean_rms), 2) if mean_rms>0 else None,
            "total_chunks": total_chunks,
            "clipped_chunks": clipped_chunks,
            "clipped_chunk_ratio": round(clipped_chunks / total_chunks, 4) if total_chunks else 0.0
        }
        return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error":"no path provided"}))
        sys.exit(2)
    path = sys.argv[1]
    try:
        out = analyze_wav(path)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except wave.Error as e:
        print(json.dumps({"error":f"wave error: {e}"}))
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"error":"file not found"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error":str(e)}))
        sys.exit(1)
