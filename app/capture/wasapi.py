"""Captura de áudio WASAPI em ``ctypes`` puro (Windows).

Existe porque o ffmpeg no Windows só enxerga dispositivos DirectShow, e a saída
do sistema (o que sai pelas caixas/headset) normalmente **não** aparece lá:
depende de "Stereo Mix", que boa parte das placas modernas — em especial
headsets USB — simplesmente não oferece. O WASAPI resolve isso de forma nativa
com a flag de *loopback*, sem instalar driver virtual nenhum.

O mesmo caminho serve para o microfone, então a captura inteira do Windows usa
uma interface só e sempre segue o dispositivo **padrão** escolhido pelo usuário
nas configurações de som — nada de adivinhar nomes de dispositivo.

Só biblioteca padrão: nada de ``comtypes``, ``pyaudio`` ou ``numpy``.
"""

from __future__ import annotations

import ctypes
import math
import threading
from array import array
from ctypes import POINTER, byref, c_int32, c_uint16, c_uint32, c_uint64, c_void_p

class _LazyOle32:
    """Resolve ``ole32`` só no primeiro uso.

    ``ctypes.windll`` não existe fora do Windows, então tocá-lo no import
    quebraria qualquer ``import`` deste módulo no Linux — inclusive o de partes
    puramente Python daqui (o resampler), usadas pelos testes multiplataforma.
    Adiando para o primeiro atributo, o módulo importa em qualquer SO e só falha
    se algo realmente tentar falar com o WASAPI.
    """

    _lib = None

    def __getattr__(self, name: str):
        if _LazyOle32._lib is None:
            _LazyOle32._lib = ctypes.windll.ole32  # type: ignore[attr-defined]
        return getattr(_LazyOle32._lib, name)


_ole32 = _LazyOle32()

# --- Constantes COM / WASAPI ---------------------------------------------
_CLSCTX_ALL = 0x17
_COINIT_MULTITHREADED = 0x0
_RPC_E_CHANGED_MODE = -2147417850  # 0x80010106
_STGM_READ = 0

_SHAREMODE_SHARED = 0
_STREAMFLAGS_LOOPBACK = 0x00020000
_STREAMFLAGS_AUTOCONVERTPCM = 0x80000000
_STREAMFLAGS_SRC_DEFAULT_QUALITY = 0x08000000
_BUFFERFLAGS_SILENT = 0x2
_DEVICE_STATE_ACTIVE = 0x1
_BUFFER_DURATION_100NS = 20_000_000  # 2 s de folga no buffer do endpoint

#: ``IAudioClient`` perdeu o dispositivo (headset desligado, troca de saída).
AUDCLNT_E_DEVICE_INVALIDATED = -2004287484  # 0x88890004

E_RENDER, E_CAPTURE = 0, 1
_ROLE_CONSOLE = 0

_WAVE_FORMAT_PCM = 0x0001
_WAVE_FORMAT_IEEE_FLOAT = 0x0003
_WAVE_FORMAT_EXTENSIBLE = 0xFFFE

#: Taxa que o whisper consome, igual à do Linux.
TARGET_RATE = 16000


class GUID(ctypes.Structure):
    _fields_ = [("Data1", c_uint32), ("Data2", c_uint16),
                ("Data3", c_uint16), ("Data4", ctypes.c_ubyte * 8)]

    def __init__(self, text: str | None = None) -> None:
        super().__init__()
        if not text:
            return
        # Parse em Python puro, sem ``CLSIDFromString``: as GUIDs constantes são
        # montadas no import do módulo, e chamar o ole32 aí quebraria o import no
        # Linux. O formato é ``{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}``.
        cleaned = text.strip().strip("{}")
        parts = cleaned.split("-")
        if len(parts) != 5:
            raise ValueError(f"GUID inválido: {text}")
        try:
            self.Data1 = int(parts[0], 16)
            self.Data2 = int(parts[1], 16)
            self.Data3 = int(parts[2], 16)
            raw = bytes.fromhex(parts[3] + parts[4])
        except ValueError as exc:
            raise ValueError(f"GUID inválido: {text}") from exc
        if len(raw) != 8:
            raise ValueError(f"GUID inválido: {text}")
        self.Data4 = (ctypes.c_ubyte * 8)(*raw)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GUID):
            return NotImplemented
        return bytes(self) == bytes(other)

    __hash__ = None  # type: ignore[assignment]


class WAVEFORMATEX(ctypes.Structure):
    # ``_pack_ = 1`` não é decoração: o SDK declara estas structs sob
    # ``pshpack1.h``. Sem isso o ctypes alinha WAVEFORMATEX em 20 bytes em vez
    # de 18, o SubFormat de WAVEFORMATEXTENSIBLE sai deslocado em 4 bytes e a
    # detecção de float32 falha justamente no formato de mix mais comum.
    _pack_ = 1
    _fields_ = [("wFormatTag", c_uint16), ("nChannels", c_uint16),
                ("nSamplesPerSec", c_uint32), ("nAvgBytesPerSec", c_uint32),
                ("nBlockAlign", c_uint16), ("wBitsPerSample", c_uint16),
                ("cbSize", c_uint16)]


class WAVEFORMATEXTENSIBLE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("Format", WAVEFORMATEX), ("Samples", c_uint16),
                ("dwChannelMask", c_uint32), ("SubFormat", GUID)]


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [("fmtid", GUID), ("pid", c_uint32)]


class PROPVARIANT(ctypes.Structure):
    # No x64 a união começa no offset 8; para VT_LPWSTR basta ler o ponteiro.
    _fields_ = [("vt", c_uint16), ("_r1", c_uint16), ("_r2", c_uint16), ("_r3", c_uint16),
                ("pwszVal", ctypes.c_wchar_p), ("_pad", c_void_p)]


_CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
_IID_IMMDeviceEnumerator = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
_IID_IAudioClient = GUID("{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}")
_IID_IAudioCaptureClient = GUID("{C8ADBD64-E71E-48A0-A4DE-185C395CD317}")
_IID_IPropertyStore = GUID("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}")
_IID_IUnknown = GUID("{00000000-0000-0000-C000-000000000046}")
_IID_IAgileObject = GUID("{94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90}")
_IID_IActivateAudioInterfaceCompletionHandler = GUID("{41D949AB-9862-444A-80F6-C261334DA5EB}")
_SUBTYPE_PCM = GUID("{00000001-0000-0010-8000-00AA00389B71}")
_SUBTYPE_IEEE_FLOAT = GUID("{00000003-0000-0010-8000-00AA00389B71}")
_PKEY_Device_FriendlyName = PROPERTYKEY(
    GUID("{A45C254E-DF1C-4EFD-8020-67D146A850E0}"), 14)

_VT_BLOB = 65
_PROCESS_LOOPBACK_INCLUDE = 0
_PROCESS_LOOPBACK_EXCLUDE = 1
_VIRTUAL_PROCESS_LOOPBACK = "VAD\\Process_Loopback"


class _AudioClientActivationParams(ctypes.Structure):
    _fields_ = [("activation_type", c_int32), ("target_process_id", c_uint32), ("process_loopback_mode", c_int32)]


class _Blob(ctypes.Structure):
    _fields_ = [("size", c_uint32), ("data", POINTER(ctypes.c_ubyte))]


class _PropVariantBlob(ctypes.Structure):
    _fields_ = [("vt", c_uint16), ("reserved1", c_uint16), ("reserved2", c_uint16),
                ("reserved3", c_uint16), ("blob", _Blob)]


class WasapiError(OSError):
    """Falha numa chamada COM do WASAPI, com o HRESULT preservado."""

    def __init__(self, what: str, hr: int) -> None:
        self.hr = hr
        super().__init__(f"{what} falhou (HRESULT 0x{hr & 0xFFFFFFFF:08X})")


def _call(ptr: c_void_p, index: int, types: tuple, *args) -> int:
    """Invoca o método ``index`` da vtable de uma interface COM."""
    vtable = ctypes.cast(ptr, POINTER(POINTER(c_void_p))).contents
    proto = ctypes.WINFUNCTYPE(c_int32, c_void_p, *types)
    return proto(vtable[index])(ptr, *args)


def _check(hr: int, what: str) -> int:
    if hr < 0:
        raise WasapiError(what, hr)
    return hr


def _release(ptr: c_void_p | None) -> None:
    if ptr:
        _call(ptr, 2, ())


def ensure_com() -> None:
    """``CoInitializeEx`` idempotente para a thread atual."""
    hr = _ole32.CoInitializeEx(None, _COINIT_MULTITHREADED)
    if hr < 0 and hr != _RPC_E_CHANGED_MODE:
        raise WasapiError("CoInitializeEx", hr)


def _device_enumerator() -> c_void_p:
    enum = c_void_p()
    _check(_ole32.CoCreateInstance(byref(_CLSID_MMDeviceEnumerator), None, _CLSCTX_ALL,
                                   byref(_IID_IMMDeviceEnumerator), byref(enum)),
           "CoCreateInstance(MMDeviceEnumerator)")
    return enum


def _friendly_name(device: c_void_p) -> str:
    store = c_void_p()
    if _call(device, 4, (c_uint32, POINTER(c_void_p)), _STGM_READ, byref(store)) < 0:
        return "(sem nome)"
    try:
        value = PROPVARIANT()
        if _call(store, 5, (POINTER(PROPERTYKEY), POINTER(PROPVARIANT)),
                 byref(_PKEY_Device_FriendlyName), byref(value)) < 0:
            return "(sem nome)"
        name = value.pwszVal or "(sem nome)"
        ctypes.windll.ole32.PropVariantClear(byref(value))
        return name
    finally:
        _release(store)


def list_endpoints(flow: int) -> list[str]:
    """Nomes amigáveis dos endpoints ativos (``E_RENDER`` ou ``E_CAPTURE``)."""
    ensure_com()
    enum = _device_enumerator()
    collection = c_void_p()
    names: list[str] = []
    try:
        _check(_call(enum, 3, (c_uint32, c_uint32, POINTER(c_void_p)),
                     flow, _DEVICE_STATE_ACTIVE, byref(collection)), "EnumAudioEndpoints")
        count = c_uint32()
        _check(_call(collection, 3, (POINTER(c_uint32),), byref(count)), "GetCount")
        for i in range(count.value):
            device = c_void_p()
            if _call(collection, 4, (c_uint32, POINTER(c_void_p)), i, byref(device)) < 0:
                continue
            try:
                names.append(_friendly_name(device))
            finally:
                _release(device)
    finally:
        _release(collection)
        _release(enum)
    return names


def default_endpoint_name(flow: int) -> str | None:
    """Nome do endpoint padrão, ou ``None`` se não houver nenhum."""
    ensure_com()
    enum = _device_enumerator()
    device = c_void_p()
    try:
        if _call(enum, 4, (c_uint32, c_uint32, POINTER(c_void_p)),
                 flow, _ROLE_CONSOLE, byref(device)) < 0:
            return None
        return _friendly_name(device)
    finally:
        _release(device)
        _release(enum)


class _BoxResampler:
    """Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.

    Média simples em vez de um filtro FIR: para voz a 16 kHz a diferença é
    inaudível para o whisper, e evita depender de numpy/scipy.
    """

    def __init__(self, src_rate: int, dst_rate: int = TARGET_RATE) -> None:
        self.ratio = src_rate / dst_rate
        self._pending = array("f")
        self._pos = 0.0

    def feed(self, mono: array) -> array:
        if mono:
            self._pending.extend(mono)
        out = array("f")
        pos = self._pos
        total = len(self._pending)
        while True:
            start = int(pos)
            end = int(pos + self.ratio)
            if end > total:
                break
            if end > start:
                chunk = self._pending[start:end]
                out.append(sum(chunk) / len(chunk))
            else:
                out.append(self._pending[start])
            pos += self.ratio
        consumed = int(pos)
        if consumed:
            del self._pending[:consumed]
        self._pos = pos - consumed
        return out


class WasapiCapture:
    """Um fluxo de captura: microfone padrão ou loopback da saída padrão.

    A saída de :meth:`read` já vem em mono 16 kHz (float em -1..1), pronta para
    ser somada com a de outro fluxo.
    """

    def __init__(self, loopback: bool) -> None:
        self.loopback = loopback
        self.device_name: str | None = None
        self.native_rate: int | None = None
        self.native_channels: int | None = None
        self._enum: c_void_p | None = None
        self._device: c_void_p | None = None
        self._client: c_void_p | None = None
        self._capture: c_void_p | None = None
        self._fmt: WAVEFORMATEX | None = None
        self._pfmt = None
        self._is_float = False
        self._bytes_per_sample = 4
        self._resampler: _BoxResampler | None = None

    # --- ciclo de vida ---------------------------------------------------
    def open(self) -> None:
        ensure_com()
        self._enum = _device_enumerator()
        flow = E_RENDER if self.loopback else E_CAPTURE
        device = c_void_p()
        _check(_call(self._enum, 4, (c_uint32, c_uint32, POINTER(c_void_p)),
                     flow, _ROLE_CONSOLE, byref(device)),
               "GetDefaultAudioEndpoint")
        self._device = device
        self.device_name = _friendly_name(device)

        client = c_void_p()
        _check(_call(device, 3, (POINTER(GUID), c_uint32, c_void_p, POINTER(c_void_p)),
                     byref(_IID_IAudioClient), _CLSCTX_ALL, None, byref(client)),
               "IMMDevice::Activate")
        self._client = client

        pfmt = POINTER(WAVEFORMATEX)()
        _check(_call(client, 8, (POINTER(POINTER(WAVEFORMATEX)),), byref(pfmt)), "GetMixFormat")
        self._pfmt = pfmt
        self._adopt_format(pfmt)

        flags = _STREAMFLAGS_LOOPBACK if self.loopback else 0
        _check(_call(client, 3, (c_uint32, c_uint32, ctypes.c_int64, ctypes.c_int64,
                                 POINTER(WAVEFORMATEX), c_void_p),
                     _SHAREMODE_SHARED, flags, _BUFFER_DURATION_100NS, 0, pfmt, None),
               "IAudioClient::Initialize")

        capture = c_void_p()
        _check(_call(client, 14, (POINTER(GUID), POINTER(c_void_p)),
                     byref(_IID_IAudioCaptureClient), byref(capture)),
               "GetService(IAudioCaptureClient)")
        self._capture = capture
        _check(_call(client, 10, ()), "IAudioClient::Start")

    def _adopt_format(self, pfmt) -> None:
        fmt = pfmt.contents
        self._fmt = fmt
        self.native_rate = fmt.nSamplesPerSec
        self.native_channels = fmt.nChannels
        self._resampler = _BoxResampler(fmt.nSamplesPerSec)

        tag = fmt.wFormatTag
        if tag == _WAVE_FORMAT_EXTENSIBLE and fmt.cbSize >= 22:
            ext = ctypes.cast(pfmt, POINTER(WAVEFORMATEXTENSIBLE)).contents
            if ext.SubFormat == _SUBTYPE_IEEE_FLOAT:
                tag = _WAVE_FORMAT_IEEE_FLOAT
            elif ext.SubFormat == _SUBTYPE_PCM:
                tag = _WAVE_FORMAT_PCM

        self._bytes_per_sample = fmt.wBitsPerSample // 8
        if tag == _WAVE_FORMAT_IEEE_FLOAT and self._bytes_per_sample == 4:
            self._is_float = True
        elif tag == _WAVE_FORMAT_PCM and self._bytes_per_sample in (2, 4):
            self._is_float = False
        else:
            raise WasapiError(
                f"formato de mix não suportado (tag={fmt.wFormatTag}, "
                f"bits={fmt.wBitsPerSample})", 0)

    def close(self) -> None:
        if self._client:
            _call(self._client, 11, ())  # Stop
        if self._pfmt:
            _ole32.CoTaskMemFree(self._pfmt)
            self._pfmt = None
        _release(self._capture)
        _release(self._client)
        _release(self._device)
        _release(self._enum)
        self._capture = self._client = self._device = self._enum = None

    # --- leitura ---------------------------------------------------------
    def read(self) -> array:
        """Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).

        Um fluxo de loopback fica **sem pacote nenhum** quando não há nada
        tocando; quem chama compensa isso com silêncio pelo relógio.
        """
        if not self._capture or not self._fmt:
            raise RuntimeError("fluxo WASAPI não está aberto")

        channels = self._fmt.nChannels
        block = self._fmt.nBlockAlign
        mono = array("f")

        while True:
            packet = c_uint32()
            _check(_call(self._capture, 5, (POINTER(c_uint32),), byref(packet)),
                   "GetNextPacketSize")
            if packet.value == 0:
                break

            data = POINTER(ctypes.c_ubyte)()
            frames = c_uint32()
            flags = c_uint32()
            _check(_call(self._capture, 3,
                         (POINTER(POINTER(ctypes.c_ubyte)), POINTER(c_uint32),
                          POINTER(c_uint32), POINTER(c_uint64), POINTER(c_uint64)),
                         byref(data), byref(frames), byref(flags), None, None),
                   "GetBuffer")
            count = frames.value
            try:
                if not count:
                    continue
                if flags.value & _BUFFERFLAGS_SILENT:
                    mono.extend([0.0] * count)
                else:
                    mono.extend(self._to_mono(
                        ctypes.string_at(data, count * block), channels))
            finally:
                _check(_call(self._capture, 4, (c_uint32,), count), "ReleaseBuffer")

        assert self._resampler is not None
        return self._resampler.feed(mono)

    def _to_mono(self, raw: bytes, channels: int) -> array:
        if self._is_float:
            samples = array("f")
            samples.frombytes(raw)
        elif self._bytes_per_sample == 2:
            pcm = array("h")
            pcm.frombytes(raw)
            samples = array("f", [s / 32768.0 for s in pcm])
        else:
            pcm = array("i")
            pcm.frombytes(raw)
            samples = array("f", [s / 2147483648.0 for s in pcm])

        if channels == 1:
            return samples
        mono = array("f")
        for i in range(0, len(samples) - channels + 1, channels):
            mono.append(sum(samples[i:i + channels]) / channels)
        return mono


class _ActivationHandler:
    """Implementação mínima de IActivateAudioInterfaceCompletionHandler."""

    def __init__(self) -> None:
        query_type = ctypes.WINFUNCTYPE(c_int32, c_void_p, POINTER(GUID), POINTER(c_void_p))
        ref_type = ctypes.WINFUNCTYPE(c_uint32, c_void_p)
        completed_type = ctypes.WINFUNCTYPE(c_int32, c_void_p, c_void_p)

        class VTable(ctypes.Structure):
            _fields_ = [("QueryInterface", query_type), ("AddRef", ref_type),
                        ("Release", ref_type), ("ActivateCompleted", completed_type)]

        class Interface(ctypes.Structure):
            _fields_ = [("lpVtbl", POINTER(VTable))]

        self.event = threading.Event()
        self.client = c_void_p()
        self.result = -2147418113  # E_UNEXPECTED
        self._refs = 1

        def query(_this, iid, output):
            requested = iid.contents
            if requested in (_IID_IUnknown, _IID_IAgileObject, _IID_IActivateAudioInterfaceCompletionHandler):
                output[0] = ctypes.cast(byref(self.interface), c_void_p)
                self._refs += 1
                return 0
            output[0] = None
            return -2147467262  # E_NOINTERFACE

        def add_ref(_this):
            self._refs += 1
            return self._refs

        def release(_this):
            self._refs = max(0, self._refs - 1)
            return self._refs

        def completed(_this, operation):
            activation_result = c_int32()
            unknown = c_void_p()
            hr = _call(c_void_p(operation), 3, (POINTER(c_int32), POINTER(c_void_p)),
                       byref(activation_result), byref(unknown))
            self.result = hr if hr < 0 else activation_result.value
            if self.result >= 0:
                self.client = unknown
            elif unknown:
                _release(unknown)
            self.event.set()
            return 0

        self._callbacks = (query_type(query), ref_type(add_ref), ref_type(release), completed_type(completed))
        self.vtable = VTable(*self._callbacks)
        self.interface = Interface(ctypes.pointer(self.vtable))

    @property
    def pointer(self) -> c_void_p:
        return ctypes.cast(byref(self.interface), c_void_p)


class ProcessLoopbackCapture(WasapiCapture):
    """Loopback que inclui ou exclui a árvore de um processo do Windows."""

    def __init__(self, process_id: int, include: bool) -> None:
        super().__init__(loopback=True)
        self.process_id = process_id
        self.include = include
        self._handler: _ActivationHandler | None = None

    def open(self) -> None:
        ensure_com()
        params = _AudioClientActivationParams(
            1, self.process_id,
            _PROCESS_LOOPBACK_INCLUDE if self.include else _PROCESS_LOOPBACK_EXCLUDE,
        )
        raw_params = ctypes.cast(byref(params), POINTER(ctypes.c_ubyte))
        variant = _PropVariantBlob(_VT_BLOB, 0, 0, 0, _Blob(ctypes.sizeof(params), raw_params))
        handler = _ActivationHandler()
        operation = c_void_p()
        activate = ctypes.windll.mmdevapi.ActivateAudioInterfaceAsync
        activate.restype = c_int32
        activate.argtypes = [ctypes.c_wchar_p, POINTER(GUID), POINTER(_PropVariantBlob),
                             c_void_p, POINTER(c_void_p)]
        hr = activate(_VIRTUAL_PROCESS_LOOPBACK, byref(_IID_IAudioClient), byref(variant),
                      handler.pointer, byref(operation))
        _check(hr, "ActivateAudioInterfaceAsync")
        try:
            if not handler.event.wait(10):
                raise WasapiError("ativação do loopback por processo expirou", -1)
            _check(handler.result, "ativação do loopback por processo")
        finally:
            _release(operation)
        self._handler = handler
        self._client = handler.client
        self.device_name = f"processo {self.process_id} ({'incluir' if self.include else 'excluir'})"

        fmt = WAVEFORMATEX(_WAVE_FORMAT_PCM, 1, TARGET_RATE, TARGET_RATE * 2, 2, 16, 0)
        self._fmt = fmt
        self.native_rate = TARGET_RATE
        self.native_channels = 1
        self._bytes_per_sample = 2
        self._is_float = False
        self._resampler = _BoxResampler(TARGET_RATE)
        flags = _STREAMFLAGS_LOOPBACK | _STREAMFLAGS_AUTOCONVERTPCM | _STREAMFLAGS_SRC_DEFAULT_QUALITY
        _check(_call(self._client, 3, (c_uint32, c_uint32, ctypes.c_int64, ctypes.c_int64,
                                      POINTER(WAVEFORMATEX), c_void_p),
                     _SHAREMODE_SHARED, flags, _BUFFER_DURATION_100NS, 0, byref(fmt), None),
               "IAudioClient::Initialize(process loopback)")
        capture = c_void_p()
        _check(_call(self._client, 14, (POINTER(GUID), POINTER(c_void_p)),
                     byref(_IID_IAudioCaptureClient), byref(capture)),
               "GetService(IAudioCaptureClient)")
        self._capture = capture
        _check(_call(self._client, 10, ()), "IAudioClient::Start")

    def close(self) -> None:
        super().close()
        self._handler = None


def dbfs(peak: float) -> float:
    """Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital."""
    return -math.inf if peak <= 0 else 20 * math.log10(min(1.0, peak))
