from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


MODEL_ROOT = Path(__file__).resolve().parents[2] / "models" / "audio-intelligence"
SEGMENTATION_MODEL = MODEL_ROOT / "sherpa-onnx-pyannote-segmentation-3-0" / "model.int8.onnx"
EMBEDDING_MODEL = MODEL_ROOT / "speaker-embedding.onnx"
TAGGING_ROOT = MODEL_ROOT / "sherpa-onnx-zipformer-small-audio-tagging-2024-04-15"
TAGGING_MODEL = TAGGING_ROOT / "model.int8.onnx"
TAGGING_LABELS = TAGGING_ROOT / "class_labels_indices.csv"

EVENT_LABELS = {
    "Laughter": "risada", "Giggle": "risada", "Snicker": "risada", "Belly laugh": "risada",
    "Clapping": "aplausos", "Applause": "aplausos",
    "Crying, sobbing": "choro", "Baby cry, infant cry": "choro", "Whimper": "choro",
    "Screaming": "grito", "Yell": "grito", "Shout": "grito",
    "Music": "música",
}


def available() -> bool:
    return all(path.is_file() for path in (SEGMENTATION_MODEL, EMBEDDING_MODEL, TAGGING_MODEL, TAGGING_LABELS))


def audio_channel_count(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as source:
            return source.getnchannels()
    except (wave.Error, OSError):
        return 1


def audio_stream_count(path: Path) -> int:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(path),
        ], capture_output=True, text=True, timeout=30)
        return len([line for line in result.stdout.splitlines() if line.strip()])
    except (OSError, subprocess.SubprocessError):
        return 0


def extract_audio(video: Path, output: Path, channel: str | None = None, stream: int | None = None) -> None:
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
    ]
    if stream is not None:
        command += ["-map", f"0:a:{stream}"]
    command += ["-vn"]
    if channel:
        command += ["-af", f"pan=mono|c0={channel}"]
    command += ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0 or not output.is_file():
        raise RuntimeError((result.stderr or "não foi possível extrair o áudio")[-2000:])


def read_pcm16(path: Path):
    import numpy as np

    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getframerate() != 16000:
            raise RuntimeError("a inteligência de áudio requer WAV mono PCM 16 kHz")
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype=np.int16)
    return np.ascontiguousarray(samples.astype(np.float32) / 32768.0), 16000


#: A segmentação pyannote consome o áudio em janelas de 10 s. Um resto parcial
#: no fim faz o sherpa-onnx devolver um turno que começa depois do último
#: sample e então abortar em ComputeEmbeddings ("This segment is too short")
#: com exit(-1) — mata o processo sem lançar exceção. Completar a última janela
#: com silêncio elimina o resto parcial e o turno degenerado com ele.
SEGMENTATION_WINDOW_SECONDS = 10


def pad_to_segmentation_window(samples, sample_rate: int = 16000):
    import numpy as np

    window = SEGMENTATION_WINDOW_SECONDS * sample_rate
    missing = (-len(samples)) % window
    if not missing:
        return samples
    return np.ascontiguousarray(np.concatenate([samples, np.zeros(missing, dtype=np.float32)]))


def turns_within_duration(turns: list[dict], duration: float) -> list[dict]:
    """Descarta o que a diarização inventou sobre o silêncio de completamento."""
    result = []
    for turn in turns:
        start, end = float(turn["start"]), min(float(turn["end"]), duration)
        if end - start <= 0:
            continue
        result.append({**turn, "start": round(start, 3), "end": round(end, 3)})
    return result


def diarize(samples, sample_rate: int = 16000) -> list[dict]:
    import sherpa_onnx

    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=str(SEGMENTATION_MODEL)),
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(EMBEDDING_MODEL)),
        clustering=sherpa_onnx.FastClusteringConfig(num_clusters=-1, threshold=0.9),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not config.validate():
        raise RuntimeError("modelos de diarização inválidos")
    duration = len(samples) / sample_rate
    padded = pad_to_segmentation_window(samples, sample_rate)
    raw = sherpa_onnx.OfflineSpeakerDiarization(config).process(padded).sort_by_start_time()
    identities: dict[int, str] = {}
    result = []
    for item in raw:
        speaker = identities.setdefault(item.speaker, f"speaker_{len(identities) + 1}")
        result.append({"start": round(float(item.start), 3), "end": round(float(item.end), 3), "speaker": speaker})
    return turns_within_duration(result, duration)


def diarize_file(path: Path) -> list[dict]:
    """Diariza um WAV num processo separado.

    O sherpa-onnx chama exit(-1) de dentro do C++ quando topa com um turno
    degenerado, em vez de lançar exceção. Em processo, isso derrubava o
    pipeline inteiro e deixava a captura presa em 'processing' — reposta na
    fila e derrubando o serviço outra vez a cada rodada. Isolar a chamada
    converte o aborto num RuntimeError que o pipeline sabe tratar.
    """
    result = subprocess.run(
        [sys.executable, "-m", "app.backend.audio_intelligence", str(path)],
        capture_output=True, text=True, timeout=1800,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "sem saída").strip()[-2000:]
        raise RuntimeError(f"diarização falhou (código {result.returncode}): {detail}")
    return json.loads(result.stdout or "[]")


def _event_name(name: str) -> str | None:
    return EVENT_LABELS.get(name)


def detect_events(samples, sample_rate: int = 16000, window_seconds: float = 5, step_seconds: float = 4) -> list[dict]:
    import numpy as np
    import sherpa_onnx

    config = sherpa_onnx.AudioTaggingConfig(
        model=sherpa_onnx.AudioTaggingModelConfig(
            zipformer=sherpa_onnx.OfflineZipformerAudioTaggingModelConfig(model=str(TAGGING_MODEL)),
            num_threads=2, provider="cpu",
        ),
        labels=str(TAGGING_LABELS), top_k=8,
    )
    if not config.validate():
        raise RuntimeError("modelo de eventos acústicos inválido")
    tagger = sherpa_onnx.AudioTagging(config)
    window, step = int(window_seconds * sample_rate), int(step_seconds * sample_rate)
    detected: list[dict] = []
    for offset in range(0, len(samples), step):
        chunk = samples[offset:offset + window]
        if len(chunk) < sample_rate:
            break
        stream = tagger.create_stream()
        stream.accept_waveform(sample_rate=sample_rate, waveform=np.ascontiguousarray(chunk))
        best: dict[str, float] = {}
        for event in tagger.compute(stream):
            name = _event_name(event.name)
            if name:
                best[name] = max(best.get(name, 0), float(event.prob))
        start, end = offset / sample_rate, min(len(samples), offset + window) / sample_rate
        for name, confidence in best.items():
            threshold = 0.7 if name == "música" else 0.45
            if confidence >= threshold:
                detected.append({"start": round(start, 3), "end": round(end, 3), "event": name, "confidence": round(confidence, 3)})
    return consolidate_events(detected)


def overlapping_speech(turns: list[dict]) -> list[dict]:
    events = []
    for index, left in enumerate(turns):
        for right in turns[index + 1:]:
            if right["start"] >= left["end"]:
                break
            start, end = max(left["start"], right["start"]), min(left["end"], right["end"])
            if left["speaker"] != right["speaker"] and end - start >= 0.35:
                events.append({"start": start, "end": end, "event": "fala sobreposta", "confidence": 1.0})
    return consolidate_events(events)


def overlapping_sources(microphone: list[dict], system: list[dict]) -> list[dict]:
    events = []
    for own in microphone:
        for external in system:
            start = max(float(own["start"]), float(external["start"]))
            end = min(float(own["end"]), float(external["end"]))
            if end - start >= 0.2:
                events.append({"start": start, "end": end, "event": "fala sobreposta", "confidence": 1.0})
    return consolidate_events(events)


def consolidate_events(events: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for event in sorted(events, key=lambda item: (item["event"], item["start"])):
        if merged and merged[-1]["event"] == event["event"] and event["start"] <= merged[-1]["end"] + 1:
            merged[-1]["end"] = max(merged[-1]["end"], event["end"])
            merged[-1]["confidence"] = max(merged[-1]["confidence"], event["confidence"])
        else:
            merged.append(dict(event))
    return sorted(merged, key=lambda item: item["start"])


def overlap(start: float, end: float, other_start: float, other_end: float) -> float:
    return max(0.0, min(end, other_end) - max(start, other_start))


def enrich_segments(segments: list[dict], turns: list[dict], events: list[dict]) -> list[dict]:
    enriched = []
    for source in segments:
        item = dict(source)
        start, end = float(item.get("start", 0)), float(item.get("end", 0))
        ranked = sorted(turns, key=lambda turn: overlap(start, end, turn["start"], turn["end"]), reverse=True)
        if ranked and overlap(start, end, ranked[0]["start"], ranked[0]["end"]) > 0:
            item["speaker"] = ranked[0]["speaker"]
        item["events"] = sorted({event["event"] for event in events if overlap(start, end, event["start"], event["end"]) > 0})
        enriched.append(item)
    return enriched


def clean_speaker_turns(turns: list[dict], events: list[dict], minimum: float = 0.35) -> list[dict]:
    """Remove das falas os intervalos em que outra voz também está presente."""
    blockers = [
        (max(0.0, float(event["start"]) - 0.15), float(event["end"]) + 0.15)
        for event in events if event.get("event") == "fala sobreposta"
    ]
    cleaned: list[dict] = []
    for turn in turns:
        windows = [(float(turn["start"]), float(turn["end"]))]
        for blocked_start, blocked_end in blockers:
            next_windows = []
            for start, end in windows:
                if blocked_end <= start or blocked_start >= end:
                    next_windows.append((start, end))
                    continue
                if blocked_start - start >= minimum:
                    next_windows.append((start, min(end, blocked_start)))
                if end - blocked_end >= minimum:
                    next_windows.append((max(start, blocked_end), end))
            windows = next_windows
        cleaned += [
            {**turn, "start": start, "end": end}
            for start, end in windows if end - start >= minimum
        ]
    return cleaned


def speaker_profiles(turns: list[dict], events: list[dict] | None = None) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for turn in turns:
        grouped.setdefault(turn["speaker"], []).append(turn)
    profiles = []
    for index, (speaker, entries) in enumerate(grouped.items(), 1):
        clean_entries = clean_speaker_turns(entries, events or [])
        usable = [item for item in clean_entries if item["end"] - item["start"] >= 1.0]
        original_duration = sum(float(item["end"]) - float(item["start"]) for item in entries)
        clean_duration = sum(float(item["end"]) - float(item["start"]) for item in clean_entries)
        sample_overlapped = not usable and clean_duration < original_duration - 0.01
        best = max(usable or entries, key=lambda item: item["end"] - item["start"])
        sample_start = best["start"]
        sample_end = min(best["end"], sample_start + 8)
        profiles.append({
            "id": speaker, "label": f"Pessoa {index}",
            "sample_start": round(sample_start, 3), "sample_end": round(sample_end, 3),
            "duration": round(sum(item["end"] - item["start"] for item in entries), 3),
            "sample_overlapped": sample_overlapped,
        })
    return profiles


def speaker_embeddings(samples, turns: list[dict], events: list[dict] | None = None) -> dict[str, list[float]]:
    import numpy as np
    import sherpa_onnx

    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(sherpa_onnx.SpeakerEmbeddingExtractorConfig(
        model=str(EMBEDDING_MODEL), num_threads=1, provider="cpu",
    ))
    grouped: dict[str, list] = {}
    for turn in clean_speaker_turns(turns, events or []):
        start, end = int(turn["start"] * 16000), int(turn["end"] * 16000)
        if end > start:
            grouped.setdefault(turn["speaker"], []).append(samples[start:end])
    result = {}
    for speaker, chunks in grouped.items():
        audio = np.ascontiguousarray(np.concatenate(chunks)[:20 * 16000])
        if len(audio) < 16000:
            continue
        stream = extractor.create_stream()
        stream.accept_waveform(sample_rate=16000, waveform=audio)
        stream.input_finished()
        if extractor.is_ready(stream):
            vector = np.asarray(extractor.compute(stream), dtype=np.float32)
            norm = float(np.linalg.norm(vector))
            if norm > 0:
                result[speaker] = (vector / norm).tolist()
    return result


def embedding_for_sample(source: Path, start: float, end: float) -> list[float]:
    with tempfile.TemporaryDirectory(prefix="lume-voice-enroll-") as directory:
        wav = Path(directory) / "sample.wav"
        result = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, start):.3f}",
            "-i", str(source), "-t", f"{max(1, min(20, end-start)):.3f}", "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(wav),
        ], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError("não foi possível preparar a amostra de voz")
        samples, _ = read_pcm16(wav)
        vectors = speaker_embeddings(samples, [{"start": 0, "end": len(samples) / 16000, "speaker": "sample"}])
        if "sample" not in vectors:
            raise RuntimeError("a amostra de voz é curta ou fraca demais")
        return vectors["sample"]


def identify_profiles(profiles: list[dict], embeddings: dict[str, list[float]], known: list[dict], threshold: float = 0.72) -> None:
    for profile in profiles:
        vector = embeddings.get(profile["id"])
        if not vector:
            continue
        best, score = None, -1.0
        for identity in known:
            reference = identity.get("embedding") or []
            if len(reference) != len(vector):
                continue
            similarity = sum(float(a) * float(b) for a, b in zip(vector, reference))
            if similarity > score:
                best, score = identity, similarity
        if best and score >= threshold:
            profile.update(label=best["label"], identity_id=best["id"], confidence=round(score, 3), identified=True)


def analyze_video_audio(video: Path, transcript_segments: list[dict], known_profiles: list[dict] | None = None) -> dict:
    if not available():
        raise RuntimeError("modelos de inteligência de áudio não instalados")
    sources = {str(item.get("source")) for item in transcript_segments if item.get("source")}
    channel_count = audio_channel_count(video)
    stream_count = audio_stream_count(video)
    separated = (channel_count >= 2 or stream_count >= 4) and bool(sources & {"microphone", "discord", "system"})
    enriched: list[dict] = []
    profiles: list[dict] = []
    embeddings: dict[str, list[float]] = {}
    all_events: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="lume-audio-intelligence-") as directory:
        if separated:
            channel_map = {"discord": "c1", "system": "c2" if channel_count >= 3 else "c1"}
            stream_map = {"discord": 2, "system": 3} if stream_count >= 4 else {}
            source_segments = {
                source: [dict(item) for item in transcript_segments if item.get("source") == source]
                for source in ("microphone", "discord", "system")
            }
            for left_index, left in enumerate(("microphone", "discord", "system")):
                for right in ("microphone", "discord", "system")[left_index + 1:]:
                    all_events += overlapping_sources(source_segments[left], source_segments[right])
            for source in ("discord", "system"):
                segments = source_segments[source]
                if not segments:
                    continue
                wav = Path(directory) / f"{source}.wav"
                extract_audio(video, wav, channel=None if source in stream_map else channel_map[source], stream=stream_map.get(source))
                samples, sample_rate = read_pcm16(wav)
                turns = diarize_file(wav)
                for turn in turns:
                    turn["speaker"] = f"{source}_{turn['speaker'].rsplit('_', 1)[-1]}"
                track_events = consolidate_events(detect_events(samples, sample_rate) + overlapping_speech(turns))
                all_events += track_events
                track_enriched = enrich_segments(segments, turns, track_events)
                used = {item.get("speaker") for item in track_enriched if item.get("speaker")}
                relevant = [turn for turn in turns if turn["speaker"] in used]
                track_profiles = speaker_profiles(relevant, all_events)
                for profile in track_profiles:
                    profile["source"] = source
                track_embeddings = speaker_embeddings(samples, relevant, all_events)
                profiles += track_profiles
                embeddings.update(track_embeddings)
                enriched += track_enriched
            events = consolidate_events(all_events)
            enriched += enrich_segments(source_segments["microphone"], [], events)
        else:
            wav = Path(directory) / "audio.wav"
            extract_audio(video, wav)
            samples, sample_rate = read_pcm16(wav)
            turns = diarize_file(wav)
            events = consolidate_events(detect_events(samples, sample_rate) + overlapping_speech(turns))
            enriched = enrich_segments(transcript_segments, turns, events)
            used = {item.get("speaker") for item in enriched if item.get("speaker")}
            relevant = [turn for turn in turns if turn["speaker"] in used]
            profiles = speaker_profiles(relevant, events)
            embeddings = speaker_embeddings(samples, relevant, events)
    for item in enriched:
        item["events"] = sorted({
            event["event"] for event in events
            if overlap(float(item["start"]), float(item["end"]), event["start"], event["end"]) > 0
        })
    enriched.sort(key=lambda item: (item["start"], {"microphone": 0, "discord": 1, "system": 2}.get(item.get("source"), 9)))
    microphone_segments = [item for item in transcript_segments if item.get("source") == "microphone"]
    if separated and microphone_segments:
        best = max(microphone_segments, key=lambda item: float(item["end"]) - float(item["start"]))
        profiles.insert(0, {
            "id": "self", "label": "Você", "source": "microphone", "fixed": True,
            "identified": True, "sample_start": round(float(best["start"]), 3),
            "sample_end": round(min(float(best["end"]), float(best["start"]) + 8), 3),
            "duration": round(sum(float(item["end"]) - float(item["start"]) for item in microphone_segments), 3),
        })
    identify_profiles(profiles, embeddings, known_profiles or [])
    return {
        "segments": enriched,
        "speakers": profiles,
        "speaker_embeddings": embeddings,
        "events": events,
    }


if __name__ == "__main__":
    # Ponto de entrada de diarize_file: só o C++ isolado roda aqui, e o
    # resultado sai em JSON no stdout (os logs do sherpa vão para o stderr).
    _samples, _rate = read_pcm16(Path(sys.argv[1]))
    print(json.dumps(diarize(_samples, _rate), ensure_ascii=False))
