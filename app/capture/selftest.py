"""Self-test de captura — rode isto ao trocar de sistema.

    python -m app.capture.selftest

Ele NÃO depende do resto do app (API, banco, systemd). Serve para responder,
em ~15 s, a pergunta mais incerta do port: neste computador, dá para capturar a
saída do sistema + microfone num único WAV e tirar um screenshot? Reporta os
dispositivos encontrados, grava uma amostra e mede o volume.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from . import ScreenConfig, get_backend


def _measure_volume(ffmpeg: str, wav: Path, channel: str | None = None) -> str:
    audio_filter = "volumedetect" if channel is None else f"pan=mono|c0={channel},volumedetect"
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostdin", "-i", str(wav), "-af", audio_filter, "-f", "null", "-"],
        check=False, capture_output=True, text=True, timeout=30,
    )
    lines = [ln for ln in result.stderr.splitlines() if "mean_volume" in ln or "max_volume" in ln]
    return " / ".join(ln.split("]", 1)[-1].strip() for ln in lines) or "(sem leitura de volume)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Testa captura de áudio + tela no SO atual.")
    parser.add_argument("--seconds", type=int, default=10, help="duração da amostra de áudio")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--force", choices=["linux", "windows"], help="forçar um backend")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--no-screen", action="store_true")
    args = parser.parse_args()

    backend = get_backend(force=args.force)
    print(f"Backend selecionado: {backend.name}\n")

    print("== Janela ativa ==")
    print(f"  {backend.active_window() or '(indisponível)'}\n")

    print("== Monitores ==")
    for mon in backend.list_monitors():
        print(f"  [{mon.index}] {mon.name} {mon.geometry}")
    print()

    workdir = Path(tempfile.mkdtemp(prefix="lume-selftest-"))

    if not args.no_screen:
        print("== Tela ==")
        cfg = ScreenConfig(capture_root=workdir, active_monitor_only=False, split_monitors=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        frames = backend.grab_frame(workdir, stamp, cfg, backend.active_window() or "(teste)")
        if frames:
            for f in frames:
                print(f"  OK {f} ({f.stat().st_size} bytes)")
        else:
            print("  FALHA: nenhum frame produzido")
        print()

    if not args.no_audio:
        print("== Áudio ==")
        diag = backend.audio_diagnostics()
        print(json.dumps(diag, ensure_ascii=False, indent=2))
        if not diag.get("system_capture_ok"):
            print(f"\n  AVISO: {diag.get('hint')}")

        from .base import AudioConfig

        # `duration_seconds` faz o gravador terminar sozinho; sem isso ele roda
        # para sempre (é o modo do serviço contínuo) e o teste só terminaria
        # por timeout, antes de medir o volume.
        # 3 canais = mesmo caminho da captura contínua (mic + Discord + sistema),
        # para o self-test exercitar de fato a separação por fonte.
        audio_cfg = AudioConfig(outdir=workdir, segment_seconds=max(args.seconds, 60),
                                duration_seconds=args.seconds, channels=3)
        output = ""
        try:
            backend.audio_setup()
            argv = backend.audio_record_argv(audio_cfg)
            print(f"\n  Gravando {args.seconds}s (fale e reproduza algum som)...")
            print(f"  cmd: {' '.join(argv)}")
            try:
                done = subprocess.run(argv, check=False, capture_output=True, text=True,
                                      timeout=args.seconds + 30)
                output = (done.stderr or "").strip()
            except subprocess.TimeoutExpired:
                print("  FALHA: o gravador não terminou sozinho (timeout).")
        finally:
            backend.audio_teardown()

        if output:
            for line in output.splitlines():
                print(f"  | {line}")

        wavs = sorted(workdir.glob("audio-*.wav"))
        if wavs:
            wav = wavs[0]
            print(f"  Arquivo: {wav} ({wav.stat().st_size} bytes)")
            print(f"  Volume total: {_measure_volume(args.ffmpeg, wav)}")
            import wave

            try:
                with wave.open(str(wav)) as handle:
                    nchannels = handle.getnchannels()
            except (OSError, wave.Error):
                nchannels = 1
            if nchannels >= 3:
                for label, channel in (("microfone", "c0"), ("Discord", "c1"), ("sistema", "c2")):
                    print(f"  Volume {label} ({channel}): {_measure_volume(args.ffmpeg, wav, channel)}")
            print("\n  'max_volume: -inf dB' = silêncio digital; um número finito confirma sinal.")
        else:
            print("  FALHA: nenhum WAV gravado")

    print(f"\nArquivos do teste em: {workdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
