from __future__ import annotations

import argparse
import json
import re
import wave
from pathlib import Path


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"


def caption_chunks(text: str, limit: int = 44) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        current: list[str] = []
        for word in words:
            candidate = " ".join([*current, word])
            if current and len(candidate) > limit:
                chunks.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            chunks.append(" ".join(current))
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--audio-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--gap-seconds", type=float, default=0.8)
    args = parser.parse_args()

    segments = json.loads(args.segments.read_text(encoding="utf-8-sig"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    combined_frames: list[bytes] = []
    manifest_segments: list[dict[str, object]] = []
    subtitles: list[str] = []
    cursor = 0.0
    reference_params = None

    for index, segment in enumerate(segments, start=1):
        audio_path = args.audio_directory / f"segment-{index:02}.wav"
        with wave.open(str(audio_path), "rb") as source:
            params = source.getparams()
            frames = source.readframes(params.nframes)
        current_format = (params.nchannels, params.sampwidth, params.framerate)
        if reference_params is None:
            reference_params = current_format
        if current_format != reference_params:
            raise ValueError("all narration segments must share one PCM format")

        duration = params.nframes / params.framerate
        start = cursor
        end = start + duration
        combined_frames.append(frames)
        chunks = caption_chunks(segment["text"])
        total_words = sum(len(chunk.split()) for chunk in chunks)
        chunk_cursor = start
        for chunk in chunks:
            share = len(chunk.split()) / total_words
            chunk_end = min(end, chunk_cursor + (duration * share))
            subtitles.extend(
                [
                    str(len([line for line in subtitles if line.isdigit()]) + 1),
                    f"{srt_time(chunk_cursor)} --> {srt_time(chunk_end)}",
                    chunk,
                    "",
                ]
            )
            chunk_cursor = chunk_end
        manifest_segments.append(
            {
                "index": index,
                "action": segment["action"],
                "text": segment["text"],
                "duration_seconds": round(duration, 3),
                "gap_seconds": args.gap_seconds if index < len(segments) else 0,
            }
        )
        cursor = end
        if index < len(segments):
            silence_frames = round(args.gap_seconds * params.framerate)
            combined_frames.append(
                b"\0" * silence_frames * params.nchannels * params.sampwidth
            )
            cursor += args.gap_seconds

    if reference_params is None:
        raise ValueError("at least one narration segment is required")
    channels, sample_width, frame_rate = reference_params
    with wave.open(str(args.output_directory / "narration.wav"), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(sample_width)
        output.setframerate(frame_rate)
        output.writeframes(b"".join(combined_frames))

    (args.output_directory / "captions.srt").write_text(
        "\n".join(subtitles), encoding="utf-8"
    )
    manifest = {
        "schema_version": "good-neighbor.video.v1",
        "total_duration_seconds": round(cursor, 3),
        "segments": manifest_segments,
    }
    (args.output_directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps({"duration_seconds": manifest["total_duration_seconds"]}))


if __name__ == "__main__":
    main()
