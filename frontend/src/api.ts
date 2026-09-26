export type ScreenSettings = {
  capture_mode: "interval" | "change";
  interval_seconds: number;
  change_poll_seconds: number;
  change_threshold_percent: number;
  change_max_interval_seconds: number;
  max_geometry: string;
  split_monitors: boolean;
  active_monitor_only: boolean;
  privacy_fail_closed: boolean;
};

export type AppMode = "completo" | "lumini";
export type Status = {
  /** `lumini` é a instalação só-gravador: sem pipeline, sem Ollama, sem análise. */
  mode: AppMode;
  capturing: boolean;
  capture_paused_by_idle: boolean;
  capture_paused_by_video: boolean;
  idle: {
    supported: boolean; enabled: boolean; idle_seconds: number;
    threshold_seconds: number; captures_paused: boolean;
  };
  audio: { active: boolean; active_state: string };
  screen: { active: boolean; active_state: string };
  video: {
    enabled: boolean; service_active: boolean; active_state: string;
    recording: boolean; mode: "continuous" | "clips"; window: string; started_at: number | null; pausing_captures: boolean;
    pause_other_captures: boolean;
  };
  files: {
    audio: { count: number; bytes: number; latest: string | null };
    screen: { count: number; bytes: number; latest: string | null };
  };
  storage: { bytes: number; disk_free: number };
  settings: ScreenSettings;
};

export type Capture = {
  id: number; kind: "screen" | "audio"; source_path: string; captured_at: string;
  app: string; title: string; text: string; tags: string[]; duration_seconds: number | null;
  model: string; image_url: string | null; paired_image_url: string | null; paired_image_text: string;
  source_available: boolean;
  preserved:boolean;
  audio_channels?:number;
  capture_ids?: number[];
  transcript_segments: VideoTranscriptSegment[]; speakers: VideoSpeaker[]; audio_events: AudioEvent[];
};

export type DaySummary = {
  day: string; narrative: string; generated_at: string; model: string;
  data: {
    tasks?: { text: string; done: boolean; source: string }[];
    meetings?: { time: string; title: string; snippet: string }[];
    highlights?: string[]; app_blocks?: { app: string; minutes: number }[];
    games?: { title: string; minutes: number; event: string }[];
    relevant_media?: Record<"screens"|"audio"|"videos"|"sessions", SummaryMediaItem[]>;
  };
};
export type SummaryMediaItem = {id:number;kind:"screen"|"audio"|"video"|"session";title:string;captured_at:string;app:string;reason:string;source_path:string;preserved:boolean;available:boolean;url:string};

export type RawFile = {
  name: string; path: string; kind: "screen"|"audio"; bytes: number;
  modified_at: string; open: boolean; status: string; url: string; capture_id?:number;
  title:string; text:string; app:string; model:string; error:string;
  transcript_segments:VideoTranscriptSegment[]; speakers:VideoSpeaker[]; audio_events:AudioEvent[];
  audio_channels?:number;
  preserved:boolean;
};

export type ScreenSequenceResult = {
  title:string; narrative:string; events:string[]; tags:string[];
  key_frames:(number|string)[]; frame_count:number; model:string;
};

export type QueueItem = {
  id:number; kind:"screen"|"audio"; name:string; captured_at:string;
  status:"processing"|"pending"|"error"; error:string; position:number; stage:string; url:string;
};
export type QueueCounts = {audio:number;screen:number;processing:number;pending:number;error:number;total:number};
export type QueueSpeed = {screen:{avg_ms:number;samples:number};audio:{avg_ms:number;samples:number};eta_seconds:number|null};
export type AnalysisTrace = {time:string;kind:string;chapter?:number;title?:string;detail:string;evidence?:string[];interpretation?:string};
export type QueueJob = {detail?:string;updated_at?:string;days?:{day:string;status:string;stage:string;error?:string}[];id:string;stage:string;kind:"summary"|"hourly"|"video"|"video_session"|"screen_sequence";status?:"error"|"processing";video_id?:number;session_id?:number;sequence_id?:number;title?:string;progress?:number;trace?:AnalysisTrace[];error?:string;ai_thinking?:string;ai_content?:string;ai_metrics?:{model?:string;status?:string;prompt_tokens?:number;generated_tokens?:number;total_duration_ms?:number;eval_duration_ms?:number}};
export type PipelineQueue = {items:QueueItem[];jobs:QueueJob[];total:number;shown?:number;counts?:QueueCounts;speed?:QueueSpeed;running:boolean;worker_running?:boolean;paused?:boolean;phase:"idle"|"processing"|"summarizing";day:string};

export type HourSummary = {
  hour:string; title:string; narrative:string; tags:string[]; source_count:number; model:string; generated_at:string;
  activities:{label:string;detail:string;app:string;type:string;minutes:number}[];
};
export type ActivityFrame = {id:number;captured_at:string;title:string;text:string;preserved:boolean;available:boolean;url:string};
export type ActivitySession = {id:number;activity_key:string;day:string;app:string;title:string;narrative:string;events:string[];tags:string[];capture_ids:number[];key_capture_ids:number[];key_frames:ActivityFrame[];started_at:string;ended_at:string;source_count:number;model:string;generated_at:string};
export type ScheduleSettings = {time:string;enabled:boolean;next_run:string};
export type CleanupSettings = {enabled:boolean};
export type EditingEntry = {name:string;path:string;bytes:number;modified_at:number;edl:string};
export type EditingFolder = {root:string;exists:boolean;items:EditingEntry[];bytes:number};
export type EditingResult = {ok:boolean;name:string;path:string;fps:number;markers:number;edl:string;clips:number};
export type PromptVariable = {name:string;detail:string};
export type PromptSetting = {key:string;group:string;label:string;description:string;variables:PromptVariable[];default:string;text:string;customized:boolean};
export type StorageSettings = {
  root:string; directories:{screen:string;audio:string;video:string;clips:string};
  disk:{total:number;used:number;free:number}; candidates:StorageCandidate[]; restart_required?:boolean;
};
export type StorageCandidate = {root:string;disk:{total:number;used:number;free:number}};
export type OllamaModel = {name:string;size:number;modified_at:string;capabilities:string[]};
export type VideoSettings = {enabled:boolean;codec:"h264"|"hevc";capture_mode:"continuous"|"clips";replay_seconds:number;fps:number;geometry:string;segment_seconds:number;sample_frames:number;sample_geometry:string;retention_minutes:number;delete_after_description:boolean;pause_other_captures:boolean;focus_grace_seconds:number;analysis_profile:"fast"|"balanced"|"detailed"|"custom";scan_interval_seconds:number;max_keyframes:number;web_search_enabled:boolean;searxng_url:string;web_search_safety_limit:number;thinking_enabled:boolean;vision_model:string;text_model:string;marker_hotkey:string;marker_key_code?:string;hotkey_hold_seconds:number;marker_preroll_seconds:number;hud_enabled:boolean;hud_placement:"game"|"second"|"both";hud_corner:"top-left"|"top-right"|"bottom-left"|"bottom-right";hud_hotkey:string;hud_sound:boolean;resolve_fps:number;resolve_start_timecode:string;patterns:string[];pattern_modes:Record<string,"continuous"|"clips">;pattern_fps:Record<string,number>;pattern_geometry:Record<string,string>;pattern_sources:Record<string,"game"|"window">;service?:{active:boolean}};
export type VideoMarker = {id:number;video_id:number;offset_seconds:number;title:string;ai_generated:number;created_at:string};
export type WebSource = {title:string;url:string;snippet:string;query?:string};
export type TagStatus = "candidate" | "active" | "dormant" | "rejected";

export type TagEntry = {
  slug:string; label:string; criterion:string; status:TagStatus; origin:"model"|"user";
  proposals:number; proposal_days:number; samples:string[]; uses:number; decided_by:string;
  last_used:string|null; first_seen:string; aliases:string[]; ready:boolean;
};

export type LayaStatus = {available:boolean;socket:string;detail:string;model?:string;loaded?:boolean};

export type TagVocabulary = {
  items:TagEntry[]; laya:LayaStatus;
  settings:{min_confidence:number;min_proposals:number;min_proposal_days:number;max_active:number;dormant_days:number};
  counts:{active:number;candidate:number;dormant:number;rejected:number};
};

export type TagDecision = {
  raw:string; slug:string; label:string; applied:boolean; confidence:number; detail:string;
  outcome:"known"|"alias"|"merged"|"reactivated"|"proposed"|"discarded";
};

export type TagTestResult = {tags:string[]; decisions:TagDecision[]; laya_error:string; laya:LayaStatus};

export type TagPromotion = {
  day:string; committed:boolean; laya_error:string;
  promoted:{slug:string;label:string;criterion:string;proposals:number}[];
  merged:{slug:string;label:string;into:string;into_label:string;confidence:number}[];
  waiting:{slug:string;label:string;proposals:number;days:number}[];
  dormant:{slug:string;label:string}[];
  retired:{slug:string;label:string}[];
};

export type VideoChapter = {start?:number;end?:number;time:string;title:string;summary:string;events:string[];transcript:string;evidence?:string[];interpretation?:string;tags?:string[];app?:string;game?:string;audio_events?:AudioEvent[];web_findings?:string;web_sources?:WebSource[]};
export type VideoSpeaker = {id:string;label:string;sample_start:number;sample_end:number;duration:number;identity_id?:number;confidence?:number;identified?:boolean;confirmed?:boolean;source?:"microphone"|"discord"|"system";fixed?:boolean;sample_overlapped?:boolean};
export type VoiceIdentity = {id:number;label:string;sample_count:number;created_at:string;updated_at:string;possible_duplicates:{id:number;label:string;similarity:number}[]};
export type AudioEvent = {start:number;end:number;event:string;confidence:number};
export type VideoTranscriptSegment = {start:number;end:number;text:string;speaker?:string;events?:string[];source?:"microphone"|"discord"|"system"};
export type VideoAudioTrack = {track:number;stream_index:number;label:string;codec:string;channels:number;url:string};
export type VideoAudioTracksResult = {items:VideoAudioTrack[];status:"ready"|"preparing"|"manual"|"error";job_id?:string;error?:string;duration:number};
export type VideoFile = {id?:number;session_id?:number|null;name:string;path:string;thumbnail_url?:string;bytes:number;modified_at:string;captured_at:string;status:string;stage:string;progress:number;trace:AnalysisTrace[];title:string;game:string;game_source?:"window"|"analysis"|"unknown";description:string;context:string;transcript:string;transcript_segments:VideoTranscriptSegment[];speakers:VideoSpeaker[];audio_events:AudioEvent[];chapters:VideoChapter[];markers:VideoMarker[];error:string;preserved:boolean;available:boolean;url:string};
export type VideoSessionClip = {id:number;name:string;path:string;thumbnail_url?:string;captured_at:string;title:string;game:string;game_source?:"window"|"analysis"|"unknown";description:string;duration_seconds:number;bytes:number;status:string;error:string;preserved:boolean;sort_order:number;available:boolean;url:string;transcript:string;transcript_segments:VideoTranscriptSegment[];speakers:VideoSpeaker[];audio_events:AudioEvent[];chapters:VideoChapter[];markers:VideoMarker[]};
export type SharePlan = {height:number;fps:number;video_bitrate:number;audio_bitrate:number;duration:number;estimated_bytes:number};
export type LightVersion = {
  limit_mb:number;presets:number[];source_bytes:number;name:string;
  /** `fits` = o original já cabe; `absent` = ainda não foi gerada. */
  status:"fits"|"absent"|"preparing"|"ready"|"error"|"too_big";
  progress:number;bytes:number;error:string;plan:SharePlan|null;url:string;job_id?:string;
};
export type ShareHost = {name:string;label:string;max_bytes:number;permanent:boolean;expiry_options:string[]};
export type SharedLink = {id:number;url:string;host:string;bytes:number;light:boolean;limit_mb:number;expires_at:string|null;expired:boolean;created_at:string};
export type ShareUpload = {
  status:"absent"|"sending"|"done"|"error"|"cancelled";percent:number;sent_bytes:number;total_bytes:number;
  error:string;url:string;host:string;expires:string;job_id:string;
  hosts:ShareHost[];default_host:string;default_expires:string;links:SharedLink[];
};
export type VideoSession = {id:number;name:string;source_folder:string;captured_at:string;status:string;stage:string;progress:number;summary:string;context:string;preserved:boolean;clip_count:number;duration_seconds:number;bytes:number;trace:AnalysisTrace[];error:string;clips:VideoSessionClip[]};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Erro HTTP ${response.status}`);
  }
  return response.json();
}

export function uploadVideo(file:File,onProgress:(percent:number)=>void,sessionId?:number,sortOrder=0):Promise<{ok:boolean;name:string;path:string;bytes:number}> {
  return new Promise((resolve,reject)=>{
    const xhr=new XMLHttpRequest();
    xhr.open("POST",`/api/videos/import?name=${encodeURIComponent(file.name)}&client_modified_at=${encodeURIComponent(new Date(file.lastModified).toISOString())}${sessionId?`&session_id=${sessionId}&sort_order=${sortOrder}`:""}`);
    xhr.setRequestHeader("Content-Type","application/octet-stream");
    xhr.upload.onprogress=event=>{if(event.lengthComputable)onProgress(Math.round(event.loaded/event.total*100))};
    xhr.onerror=()=>reject(new Error("Falha de conexão durante o envio"));
    xhr.onload=()=>{
      let body:Record<string,unknown>={};try{body=JSON.parse(xhr.responseText||"{}")}catch{}
      if(xhr.status>=200&&xhr.status<300)resolve(body as {ok:boolean;name:string;path:string;bytes:number});
      else reject(new Error(String(body.detail||`Erro HTTP ${xhr.status}`)));
    };
    xhr.send(file);
  });
}

export const api = {
  status: () => request<Status>("/api/status"),
  capture: (action: "pause" | "resume") => request(`/api/capture/${action}`, { method: "POST" }),
  sensitive: () => request<{ patterns: string[] }>("/api/settings/sensitive"),
  saveSensitive: (patterns: string[]) => request("/api/settings/sensitive", { method: "PUT", body: JSON.stringify({ patterns }) }),
  saveSettings: (settings: ScreenSettings) => request("/api/settings/screen", { method: "PUT", body: JSON.stringify(settings) }),
  schedule: () => request<ScheduleSettings>("/api/settings/schedule"),
  saveSchedule: (settings:{time:string;enabled:boolean}) => request<ScheduleSettings>("/api/settings/schedule", {method:"PUT",body:JSON.stringify(settings)}),
  cleanupSettings: () => request<CleanupSettings>("/api/settings/cleanup"),
  saveCleanupSettings: (settings:CleanupSettings) => request<CleanupSettings>("/api/settings/cleanup", {method:"PUT",body:JSON.stringify(settings)}),
  editingFolder: () => request<EditingFolder>("/api/editing"),
  sendVideoToEditing: (id:number) => request<EditingResult>(`/api/editing/video/${id}`, {method:"POST"}),
  sendSessionToEditing: (id:number) => request<EditingResult>(`/api/editing/session/${id}`, {method:"POST"}),
  removeFromEditing: (name:string) => request<{ok:boolean;name:string}>(`/api/editing/${encodeURIComponent(name)}`, {method:"DELETE"}),
  openEditingFolder: () => request<{ok:boolean;root:string}>("/api/editing/open", {method:"POST"}),
  prompts: () => request<{items:PromptSetting[]}>("/api/settings/prompts"),
  savePrompt: (key:string,text:string) => request<PromptSetting>(`/api/settings/prompts/${key}`, {method:"PUT",body:JSON.stringify({text})}),
  resetPrompt: (key:string) => request<PromptSetting>(`/api/settings/prompts/${key}`, {method:"DELETE"}),
  storage: () => request<StorageSettings>("/api/settings/storage"),
  saveStorage: (root:string) => request<StorageSettings>("/api/settings/storage", {method:"PUT",body:JSON.stringify({root})}),
  videoSettings: () => request<VideoSettings>("/api/settings/video"),
  saveVideoSettings: (settings:VideoSettings) => request<VideoSettings>("/api/settings/video",{method:"PUT",body:JSON.stringify(settings)}),
  ollamaModels: () => request<{online:boolean;models:OllamaModel[];error?:string}>("/api/ollama/models"),
  videos: () => request<{items:VideoFile[];total:number}>("/api/videos"),
  videoAudioTracks: (path:string,prepare=false) => request<VideoAudioTracksResult>(`/api/video-audio-tracks?path=${encodeURIComponent(path)}${prepare?"&prepare=true":""}`),
  cancelVideoAudioTracks: (path:string,jobId:string) => request<{ok:boolean;cancelled:boolean}>(`/api/video-audio-tracks?path=${encodeURIComponent(path)}&job_id=${encodeURIComponent(jobId)}`,{method:"DELETE",keepalive:true}),
  videoSessions: () => request<{items:VideoSession[]}>("/api/video-sessions"),
  createVideoSession: (name:string,source_folder:string) => request<{ok:boolean;id:number;name:string}>("/api/video-sessions",{method:"POST",body:JSON.stringify({name,source_folder})}),
  joinVideoSession: (video_paths:string[],session_ids:number[],name:string) => request<{ok:boolean;id:number;name:string;clips:number;merged_sessions:number}>("/api/video-sessions/join",{method:"POST",body:JSON.stringify({video_paths,session_ids,name})}),
  createVideoMarker: (videoId:number,offset_seconds:number,title="") => request<VideoMarker>(`/api/videos/${videoId}/markers`,{method:"POST",body:JSON.stringify({offset_seconds,title})}),
  trimVideo: (videoId:number,start_seconds:number,end_seconds:number) => request<{ok:boolean;id:number;duration_seconds:number;captured_at:string;analysis_reset:boolean}>(`/api/videos/${videoId}/trim`,{method:"POST",body:JSON.stringify({start_seconds,end_seconds})}),
  updateVideoMarker: (id:number,title:string) => request<{ok:boolean}>(`/api/video-markers/${id}`,{method:"PUT",body:JSON.stringify({title})}),
  deleteVideoMarker: (id:number) => request<{ok:boolean}>(`/api/video-markers/${id}`,{method:"DELETE"}),
  processVideoSession: (id:number) => request<{ok:boolean;id:number;status:string}>(`/api/video-sessions/${id}/process`,{method:"POST"}),
  cancelVideoSession: (id:number) => request<{ok:boolean;id:number}>(`/api/video-sessions/${id}/analysis`,{method:"DELETE"}),
  deleteVideoSession: (id:number) => request<{ok:boolean;id:number;clips:number;deleted_files:number}>(`/api/video-sessions/${id}`,{method:"DELETE"}),
  detachVideoFromSession: (sessionId:number,videoId:number) => request<{ok:boolean;session_id:number;video_id:number;remaining_clips:number;session_deleted:boolean}>(`/api/video-sessions/${sessionId}/clips/${videoId}`,{method:"DELETE"}),
  saveVideoSessionContext: (id:number,context:string) => request<{ok:boolean}>(`/api/video-sessions/${id}/context`,{method:"PUT",body:JSON.stringify({context})}),
  deleteVideo: (path:string) => request<{ok:boolean;path:string}>(`/api/videos?path=${encodeURIComponent(path)}`,{method:"DELETE"}),
  processVideo: (path:string) => request<{ok:boolean;status:string;id:number}>("/api/videos/process",{method:"POST",body:JSON.stringify({path})}),
  cancelVideoAnalysis: (id:number) => request<{ok:boolean;id:number}>(`/api/videos/${id}/analysis`,{method:"DELETE"}),
  saveVideoContext: (id:number,context:string) => request<{ok:boolean}>(`/api/videos/${id}/context`,{method:"PUT",body:JSON.stringify({context})}),
  saveVideoDate: (id:number,captured_at:string) => request<{ok:boolean;captured_at:string}>(`/api/videos/${id}/captured-at`,{method:"PUT",body:JSON.stringify({captured_at})}),
  renameVideoSpeaker: (videoId:number,speakerId:string,label:string) => request<{ok:boolean}>(`/api/videos/${videoId}/speakers/${speakerId}`,{method:"PUT",body:JSON.stringify({label})}),
  renameCaptureSpeaker: (captureId:number,speakerId:string,label:string) => request<{ok:boolean}>(`/api/captures/${captureId}/speakers/${speakerId}`,{method:"PUT",body:JSON.stringify({label})}),
  voiceIdentities: () => request<{items:VoiceIdentity[]}>("/api/voice-identities"),
  deleteVoiceIdentity: (identityId:number) => request<{ok:boolean;id:number;label:string;updated:{audio:number;video:number}}>(`/api/voice-identities/${identityId}`,{method:"DELETE"}),
  downloadVideoUrl: (path:string) => `/api/video-download?path=${encodeURIComponent(path)}`,
  lightVersion: (path:string,limitMb:number) => request<LightVersion>(`/api/share/light?path=${encodeURIComponent(path)}&limit_mb=${limitMb}`),
  startLightVersion: (path:string,limitMb:number) => request<LightVersion>(`/api/share/light?path=${encodeURIComponent(path)}&limit_mb=${limitMb}`,{method:"POST"}),
  cancelLightVersion: (path:string) => request<{ok:boolean;cancelled:number}>(`/api/share/light?path=${encodeURIComponent(path)}`,{method:"DELETE",keepalive:true}),
  shareUpload: (path:string) => request<ShareUpload>(`/api/share/upload?path=${encodeURIComponent(path)}`),
  // `confirm_public_upload` não tem padrão de propósito: o backend recusa sem ele.
  startShareUpload: (path:string,host:string,expires:string,use_light:boolean,limit_mb:number|null) =>
    request<ShareUpload>("/api/share/upload",{method:"POST",body:JSON.stringify({path,host,expires,use_light,limit_mb,confirm_public_upload:true})}),
  cancelShareUpload: (path:string) => request<{ok:boolean;cancelled:number}>(`/api/share/upload?path=${encodeURIComponent(path)}`,{method:"DELETE",keepalive:true}),
  forgetSharedLink: (id:number) => request<{ok:boolean;id:number;unpublished:boolean}>(`/api/share/links/${id}`,{method:"DELETE"}),
  preserveVideo: (path:string) => request<{ok:boolean;path:string}>("/api/videos/preserve",{method:"POST",body:JSON.stringify({path})}),
  testAudio: () => request<{ format: Record<string, string>; mean_db: string; max_db: string; silent: boolean }>("/api/test/audio?seconds=5", { method: "POST" }),
  testScreen: () => request<{ captured: boolean; privacy_skip: boolean; message?: string; paths?: string[] }>("/api/test/screen?save=true", { method: "POST" }),
  startScreenChangeTest: (threshold_percent:number) => request<{ok:boolean;token:string;frames:number;threshold_percent:number}>("/api/test/screen-change/start", {method:"POST",body:JSON.stringify({threshold_percent})}),
  compareScreenChangeTest: (token:string,threshold_percent:number) => request<{ok:boolean;change_percent:number;threshold_percent:number;would_capture:boolean;monitors:{index:number;change_percent:number}[]}>("/api/test/screen-change/compare", {method:"POST",body:JSON.stringify({token,threshold_percent})}),
  testVideoWindow: (patterns:string[]) => request<{ok:boolean;window_id:string;title:string;window_class:string;executable:string;info:string;matched:boolean;matched_pattern:string}>("/api/test/video-window", {method:"POST",body:JSON.stringify({patterns})}),
  search: (query: string, kind: "all"|"screen"|"audio" = "all") => request<{items: Capture[]}>(`/api/search?q=${encodeURIComponent(query)}&kind=${kind}&limit=200`),
  captures: (kind: "all"|"screen"|"audio" = "all", day?:string) => request<{items: Capture[]}>(`/api/captures?kind=${kind}&limit=${day?500:200}${day?`&day=${day}`:""}`),
  days: () => request<{items:{day:string;count:number}[]}>("/api/days"),
  deleteCapture: (id:number) => request<{ok:boolean;id:number;file_deleted:boolean}>(`/api/captures/${id}`, {method:"DELETE"}),
  summary: (day: string) => request<{summary: DaySummary|null}>(`/api/summary/${day}`),
  pipelineStatus: () => request<{counts: Record<string,number>; running: boolean}>("/api/pipeline/status"),
  pipelineQueue: (day?:string) => request<PipelineQueue>(`/api/pipeline/queue?limit=300${day?`&day=${encodeURIComponent(day)}`:""}`),
  unloadOllama: () => request<{ok:boolean;models:string[];unloaded:number}>("/api/ollama/unload",{method:"POST"}),
  cancelPipeline: (day?:string) => request<{ok:boolean}>(`/api/pipeline/cancel${day?`?day=${encodeURIComponent(day)}`:""}`, {method:"POST"}),
  pausePipeline: () => request<{ok:boolean;paused:boolean;requeued:number}>("/api/pipeline/pause", {method:"POST"}),
  resumePipeline: () => request<{ok:boolean;paused:boolean;already_running:boolean}>("/api/pipeline/resume", {method:"POST"}),
  cancelEntireQueue: () => request<{ok:boolean;cancelled:number}>("/api/pipeline/queue", {method:"DELETE"}),
  cancelQueueItem: (id:number) => request<{ok:boolean}>(`/api/pipeline/queue/${id}`, {method:"DELETE"}),
  runPipeline: () => request("/api/pipeline/run", {method:"POST", body:JSON.stringify({limit_audio:10,limit_screen:100,summarize:true})}),
  enqueueUnprocessed: () => request<{ok:boolean;discovered:{audio:number;screen:number;deferred_audio?:number};requeued:number;missing:number;queued:{audio:number;screen:number;video:number;session:number;total:number};note:string}>("/api/pipeline/enqueue-unprocessed", {method:"POST"}),
  generateSummary: (day:string) => request(`/api/summary/${day}/generate`, {method:"POST"}),
  timeline: (day:string) => request<{hours:HourSummary[];source_hours:{hour:string;count:number}[];running:boolean}>(`/api/timeline/${day}`),
  activities: (day:string) => request<{items:ActivitySession[];day:string;running:boolean}>(`/api/activities/${day}`),
  generateTimeline: (day:string) => request(`/api/timeline/${day}/generate`, {method:"POST"}),
  files: (kind: "screen"|"audio", offset=0) => request<{items:RawFile[];total:number;has_more:boolean}>(`/api/files?kind=${kind}&limit=100&offset=${offset}`),
  deleteFile: (file:RawFile) => request<{ok:boolean;id:number|null;file_deleted:boolean}>(`/api/files?kind=${file.kind}&path=${encodeURIComponent(file.path)}`, {method:"DELETE"}),
  deleteUnprocessedFiles: () => request<{ok:boolean;deleted:{screen:number;audio:number};deleted_total:number;skipped:{done:number;processing:number;recording:number}}>("/api/files/unprocessed/all", {method:"DELETE"}),
  setRetention: (kind:"screen"|"audio"|"video"|"session",id:number,preserved:boolean) => request<{ok:boolean;preserved:boolean}>(`/api/retention/${kind}/${id}`,{method:"PUT",body:JSON.stringify({preserved})}),
  deleteUnkeptRawMedia: () => request<{ok:boolean;deleted:{screen:number;audio:number};deleted_total:number;deleted_bytes:number;ready_days:string[];skipped:{preserved:number;not_ready:number;active:number;missing:number}}>("/api/media/raw/unkept",{method:"DELETE"}),
  processFile: (file:RawFile) => request<{status:string;title?:string}>("/api/pipeline/process-file", {method:"POST",body:JSON.stringify({kind:file.kind,path:file.path})}),
  testScreenSequence: (paths:string[]) => request<{ok:boolean;status:string;id:number}>("/api/test/screen-sequence", {method:"POST",body:JSON.stringify({paths})}),
  screenSequenceResult: (id:number) => request<{id:number;status:string;stage:string;progress:number;error:string;result:ScreenSequenceResult}>(`/api/test/screen-sequence/${id}`),
  cancelScreenSequence: (id:number) => request<{ok:boolean;id:number}>(`/api/test/screen-sequence/${id}`, {method:"DELETE"}),
  tags: () => request<TagVocabulary>("/api/tags"),
  createTag: (label:string, criterion:string) => request<{slug:string;label:string;criterion:string}>("/api/tags", {method:"POST", body:JSON.stringify({label, criterion})}),
  testTags: (tags:string[], context:string, use_laya:boolean) => request<TagTestResult>("/api/tags/test", {method:"POST", body:JSON.stringify({tags, context, use_laya})}),
  promoteTags: (day:string, commit:boolean) => request<TagPromotion>(`/api/tags/promote?day=${encodeURIComponent(day)}&commit=${commit}`, {method:"POST"}),
  setTagStatus: (slug:string, status:TagStatus) => request<{slug:string;status:string}>(`/api/tags/${encodeURIComponent(slug)}/status`, {method:"PUT", body:JSON.stringify({status})}),
  mergeTag: (slug:string, into:string) => request<{slug:string;into:string;label:string}>(`/api/tags/${encodeURIComponent(slug)}/merge`, {method:"POST", body:JSON.stringify({into})}),
  deleteTagAlias: (alias:string) => request<{alias:string}>(`/api/tags/aliases/${encodeURIComponent(alias)}`, {method:"DELETE"}),
};
