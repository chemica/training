#!/usr/bin/env python3
"""Render numbered lesson narration scripts with Piper and real pause markers."""

from __future__ import annotations

import argparse
import re
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


PAUSE = re.compile(r"\[PAUSE (\d+)s\]")


def render_lesson(
    voice: PiperVoice,
    source: Path,
    destination: Path,
    synthesis: SynthesisConfig,
    sentence_silence: float,
) -> float:
    pieces = PAUSE.split(source.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    frames_written = 0
    sample_rate = voice.config.sample_rate
    sample_width = 2
    channels = 1

    with wave.open(str(destination), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(sample_width)
        output.setframerate(sample_rate)

        for index, piece in enumerate(pieces):
            if index % 2:
                seconds = int(piece)
                silence = b"\x00" * seconds * sample_rate * sample_width * channels
                output.writeframes(silence)
                frames_written += seconds * sample_rate
                continue

            text = piece.strip()
            if not text:
                continue
            chunks = list(voice.synthesize(text, synthesis))
            for chunk_index, chunk in enumerate(chunks):
                if (chunk.sample_rate, chunk.sample_width, chunk.sample_channels) != (
                    sample_rate,
                    sample_width,
                    channels,
                ):
                    raise ValueError(f"Unexpected audio format in {source}")
                output.writeframes(chunk.audio_int16_bytes)
                frames_written += len(chunk.audio_int16_bytes) // (sample_width * channels)
                if chunk_index < len(chunks) - 1:
                    gap_frames = round(sentence_silence * sample_rate)
                    output.writeframes(b"\x00" * gap_frames * sample_width * channels)
                    frames_written += gap_frames

    return frames_written / sample_rate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--piper-home",
        type=Path,
        default=Path("/home/ben/training/voice-synthesis"),
    )
    parser.add_argument("--length-scale", type=float, default=0.95)
    parser.add_argument("--sentence-silence", type=float, default=0.15)
    parser.add_argument("lessons", nargs="*", help="Optional four-digit lesson numbers")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    source_dir = project / "audio" / "scripts"
    output_dir = project / "audio" / "generated" / "lessons"
    model = args.piper_home / "voices" / "en_GB-alba-medium.onnx"
    if not model.exists() or not model.with_suffix(".onnx.json").exists():
        raise SystemExit(f"Missing Alba model or configuration under {model.parent}")

    sources = sorted(source_dir.glob("[0-9][0-9][0-9][0-9]-*.txt"))
    if args.lessons:
        wanted = {number.zfill(4) for number in args.lessons}
        sources = [source for source in sources if source.name[:4] in wanted]
    if not sources:
        raise SystemExit("No matching narration scripts found")

    print(f"Loading Alba from {model}", flush=True)
    voice = PiperVoice.load(model)
    synthesis = SynthesisConfig(length_scale=args.length_scale)
    for source in sources:
        destination = output_dir / f"{source.stem}.wav"
        if destination.exists() and destination.stat().st_mtime >= source.stat().st_mtime:
            print(f"Current {destination.name}", flush=True)
            continue
        print(f"Rendering {source.name}", flush=True)
        duration = render_lesson(
            voice,
            source,
            destination,
            synthesis,
            args.sentence_silence,
        )
        print(f"  {destination.name}: {duration / 60:.1f} minutes", flush=True)


if __name__ == "__main__":
    main()
