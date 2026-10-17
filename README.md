# Hey Slides — local speech recognition prototype

Working direction: English speech-to-text with a pretrained local Vosk model,
an explicit **Hey Slides** command prefix, an internal five-slide viewer,
and a Windows PowerPoint slideshow adapter.
Pretrained models were accepted by the lecturer according to the student on
17 October 2026. The exact acceptance of the separate manual-feature branch
still needs to be established.

## Run on this computer

Double-click **Start Prototype.cmd**, or use PowerShell:

```powershell
cd 'C:\Binus Semester 5\Speech Recognition\voice-slide'
& '.venv\Scripts\python.exe' -m app.main
```

Choose a microphone, click **Start listening**, and speak English. Audio is
processed locally. The microphone stays off until Start is clicked.

- `Hey Slides, next slide`
- `Hey Slides, previous slide`
- `Hey Slides, next slides` / `Hey Slides, previous slides` (plural variants)
- `Hey Slides, go to slide five`
- `Hey Slides, go to slide one two` (slide 12)
- Alternatively say `Hey Slides`, pause, then say `next slide` within four
  seconds **after the prefix is finalized**.
- Every new command needs the prefix. Other complete phrases are only transcribed.
- The text-only parser check bypasses recognition and is clearly labeled in the
  transcript/action history; it is for debugging, not proof of ASR accuracy.
- Stop disables actions immediately. Any remaining recognized text is preserved
  without executing it.

## PowerPoint Windows (Phase 6)

1. Install the updated dependencies with the command below if this is an older checkout.
2. Open your presentation in **Windows desktop PowerPoint** and start its slideshow
   (F5, or Shift+F5 from the current slide). Use **All slides** in Set Up Slide Show.
3. In Hey Slides choose **PowerPoint**, then click **Connect / refresh PowerPoint**.
   Exactly one slideshow must be running when you connect.
4. Check the connected presentation name and slide number, then click **Start listening**.
5. Say a complete command, then pause so recognition can finalize it.

```powershell
& '.venv\Scripts\python.exe' -m pip install -r requirements-prototype.txt
```

The left panel shows the last slide index read back from PowerPoint, not a slide
thumbnail or continuous screen capture. Connect/refresh updates it after manual
navigation; each action also reads the current index again before moving.
Buttons and the text-only parser check use the selected target too.

Next/previous navigate to a **different slide**, skip hidden slides, and stop at
the boundaries without ending the show. They do not step through individual
animations. An explicit go-to command can target a hidden slide. Number input
supports written digits 1–999, spoken cardinal numbers 1–99, or up to three
spoken digits (`one zero zero` = 100). The actual deck length limits the target.
`one hundred` and custom/range shows are not supported in this version.

The adapter uses COM directly, so keystrokes do not depend on the foreground
application. It attaches to the selected running show, never opens/saves/closes
your presentation, and never falls back to demo navigation on a failure. If the
show ends, changes identity, or PowerPoint becomes unavailable, reconnect before
continuing. Closing Office dialogs may resolve busy errors. Switching targets or
reconnecting stops microphone listening and clears command authorization. Stop
prevents later queued recognition events from dispatching actions; it does not
undo a command already dispatched to PowerPoint.

## Fresh installation (Python 3.12 recommended)

```powershell
python -m venv .venv
& '.venv\Scripts\python.exe' -m pip install -r requirements-prototype.txt
& '.venv\Scripts\python.exe' -m scripts.download_model
& '.venv\Scripts\python.exe' -m scripts.check_prototype
& '.venv\Scripts\python.exe' -m app.main
```

The default Light English model download is about 40 MB; installation requires internet,
but recognition does not. The app never downloads models automatically or sends
audio to a cloud API. Use `requirements-prototype.txt` and `check_prototype` for
this version. The original `requirements.txt`, dataset scripts, root planning
documents, and Bab 1–3 draft describe the earlier MFCC/SVM direction and have
not yet been consolidated or rewritten.

## Recognition quality and model comparison (Phase 7a)

The **ASR model** selector offers two unrestricted English recognizers:

| Profile | Model | Download |
|---|---|---|
| Light English (default / original baseline) | vosk-model-small-en-us-0.15 | About 40 MB |
| Balanced English (experimental) | vosk-model-en-us-0.22-lgraph | About 128 MB |

Vosk publishes lower errors for the balanced model on its listed LibriSpeech and
TED-LIUM benchmarks. This motivates trying it, but does not prove improvement
on your accent, microphone, or room. It also costs more CPU/memory; the model
download size is not its runtime memory usage. Both modes retain full English
transcription; neither forces every utterance into our command vocabulary.

**Live-stream caveat:** the balanced model passed offline decoding, but real-time
synthetic callback replay on the development computer exceeded stale-audio limits,
including a trial at 2500 ms. It is therefore experimental and is **not the new
default or a validated fix**. Prefer offline recording comparison first. In live
mode it may stop rather than execute a delayed action. The final limits are
500 ms / 12 queued blocks for Light and 1000 ms / 48 blocks for Balanced;
limits apply before and after decoding. These limits are safeguards, not achieved
latencies. No claim of 200 ms compliance follows from either setting.

Stop listening before changing models. The model is reloaded on the next Start.
Missing models produce an installation instruction instead of silently falling
back to another recognizer. To install either profile explicitly:

```powershell
& '.venv\Scripts\python.exe' -m scripts.download_model --profile balanced
& '.venv\Scripts\python.exe' -m scripts.download_model --profile light
```

For the first real test, say **Hey Slides, next slide** as one phrase, then pause.
Repeat with **previous slide**. Singular and plural slide commands are accepted,
but the prefix is still required. Wrong words such as `next line` or `a slight`
are not automatically rewritten into commands; guessing those could cause false
actions. A correctly transcribed command can still be rejected if additional
words are included in the same utterance, because the grammar remains strict.

The input-level label reports RMS in dBFS. `quiet / no speech` below -40 dBFS and
the near-clipping indicator are diagnostic heuristics, not calibrated loudness,
SNR, or confidence scores. Silence naturally appears quiet. Check the level
**while speaking**: persistently quiet speech suggests checking the selected
microphone, distance, and Windows input gain. Clipping suggests reducing gain.
Audio-level summaries and the selected model profile are included in local logs;
raw microphone audio is still not recorded.

When using Remote Desktop, ensure the selected input actually carries your
forwarded microphone rather than the remote computer's room microphone. Compare
with a direct local microphone test if possible. The application cannot infer
this routing from a wrong transcript.

For a repeatable comparison of the same real recording:

```powershell
& '.venv\Scripts\python.exe' -m scripts.transcribe_wav 'your-recording.wav' --profile light --output 'logs\light.json'
& '.venv\Scripts\python.exe' -m scripts.transcribe_wav 'your-recording.wav' --profile balanced --output 'logs\balanced.json'
```

Compare reference text, command success, ordinary-speech false actions, and
processing time. Swapping models is not training or fine-tuning. The separate
manual MFCC branch remains separate and unchanged.

## Architecture and manual features

```text
Microphone (16 kHz mono PCM16, 25 ms blocks)
  -> bounded audio queue -> local Vosk recognizer
  -> partial/completed transcript -> strict completed-phrase parser
  -> selected target: internal slide viewer OR PowerPoint COM adapter
  -> slide state read-back / explicit error

Same audio -> one-second rolling buffer -> manual NumPy MFCC -> feature panel
```

`app/features.py` explicitly implements framing (25 ms / 10 ms hop), Hamming
window, FFT power spectrum (512 points), 40 triangular HTK-Mel filters,
natural log energies, and orthonormal DCT-II (13 coefficients). Delta and
delta-delta use edge replication; mean/std/min/max pooling produces 156 values.
There is no pre-emphasis, liftering, or automatic gain normalization in this
educational branch. Incomplete frames are not centered or filled with future
audio; very short inputs are padded to one frame. Heatmap normalization is for
display only. The optional save button exports features and metadata to JSON.

**These manual features are not the inputs to Vosk.** Vosk's pretrained model
uses its own internal feature pipeline. Allowing pretrained models does not by
itself establish that this arrangement meets the lecturer's manual-extraction
requirement. If the manually extracted features must drive recognition, the
recognizer integration needs a separate design decision. We do not claim that
the current app implements full ASR from our own MFCC features.

## Timing and known limits

- Decode call time, MFCC analysis time, and queue age are separate measurements.
  None is the complete time from a spoken word ending to text appearing.
- Commands execute only on completed utterances. Endpoint detection may wait
  for silence. The maximum 200 ms target is **not validated** and this initial
  implementation may exceed it.
- No keyword-restricted grammar is supplied to Vosk: ordinary English can be
  transcribed, within the selected model's vocabulary and accuracy limitations.
- Strict parsing intentionally rejects embedded/negated/extra-word phrases.
  It cannot understand intent; an example command spoken exactly like a real
  command can still trigger. Recognition mistakes can miss or falsely produce
  a prefix. Actual recordings and user testing are necessary.
- Repeated partial hypotheses never trigger actions. Replayed final event IDs
  are ignored; separate identical commands remain valid.
- The audio queue is bounded. Overflow or excessive backlog stops listening
  instead of dispatching commands from stale audio. Devices must support 16 kHz
  mono input; select another input if the driver rejects this format.
- Canva integration, model comparison, and user
  study are not included yet. Previous project report sections need revision before
  submission because the model choice and scope have changed.

## Checks and reproducible file decoding

```powershell
& '.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '.venv\Scripts\python.exe' -m scripts.check_prototype
& '.venv\Scripts\python.exe' -m scripts.verify_ui
& '.venv\Scripts\python.exe' -m scripts.transcribe_wav 'your-recording.wav' --output 'logs\file-result.json'
```

WAV input must be uncompressed mono 16 kHz, signed 16-bit PCM. Add `--realtime`
to feed samples at audio speed. File replay uses the same recognizer/parser;
its EOF flush is labeled and is not proof of live recognition latency.
Unit tests verify command rules and DSP properties, not recognition quality.

The PowerPoint unit tests use COM-like fakes and the UI integration check does
not open Office. To opt into a real adapter check, close PowerPoint first and run:

```powershell
& '.venv\Scripts\python.exe' -m scripts.verify_powerpoint_live --run
```

This creates only an unsaved blank test presentation, checks actual navigation
and closed-show rejection, and closes its own fixture. It refuses to run if
PowerPoint is already running. It does not capture speech or measure spoken
command latency. `adapter_ms` in action logs measures the COM call and slide-index
read-back, not visible rendering completion or word-to-action latency.

Session logs contain recognized text, decisions, action sources, and processing
measurements in local `logs/*.jsonl`. Raw microphone audio is not saved. Logs
and downloaded models are ignored by Git. Synthetic-audio smoke tests, if
present in logs, are engineering checks and must not be reported as user-study
results or real-speaker WER.

### Verified during initial development, 17 October 2026

- 14 unit tests passed, covering command authorization, replay suppression,
  intentional repeats, boundaries, and MFCC mathematical properties.
- Desktop widget/event smoke checks passed, including partial text not executing
  and a final event queued before Stop not causing an action afterward.
- Runtime packages and the local model loaded successfully. The default input
  device reported support for 16 kHz mono PCM16; actual live microphone
  recognition still needs the student's spoken test.
- Windows synthetic speech was decoded by the actual Vosk model: the ordinary
  sentence was transcribed without an action, and both Hey Slides commands were
  transcribed and parsed correctly. Initial short files finalized at EOF;
  this is not evidence of live endpoint response time or accuracy on real users.
- A continuous synthetic recording with silence between the three phrases also
  produced the expected ordinary/next/previous results through normal endpoint
  finalization, without relying on EOF to finalize those phrases.

### Phase 6 verification, 17 October 2026

- Command/feature/PowerPoint unit checks and desktop integration checks passed.
  Adapter fakes cover connection failures, hidden slides, manual navigation,
  read-back mismatch, stale show identity, slide boundaries, and invalid numbers.
- A separate real PowerPoint run passed: 1 → 3 skipped hidden slide 2,
  previous returned to 1, go-to reached 4, next at the last slide kept it at 4,
  and a command after ending the show was rejected. No user presentation was used.
- This validates the adapter, not recognition of a real user's voice. The 200 ms
  requirement, accents/noise, and the manual-feature requirement still need evaluation.

### Phase 7a engineering checks, 17 October 2026

- Both official model profiles loaded and transcribed the same continuous
  synthetic recording. The ordinary sentence produced no action, and next /
  previous phrases produced the expected parser decisions with both models.
  These samples do not establish that either model is better for the student.
- Real-time callback replay exposed unacceptable decode bursts for the balanced
  model. Light remains the default; the balanced model is an offline comparison
  candidate and experimental live option. Further model/decoder work is needed.
- Model-path selection, reload-on-profile-change, plural command handling,
  input indicators, and existing regression/UI checks passed.
- Real recordings, comparison metrics, the user study, and latency evaluation
  remain outstanding. Phase 7 as a whole is not complete.

## Phase commits

The prototype baseline (Phases 2–5) is commit `8e272ec`. Phase 6 adds PowerPoint
control and slide-number commands. Phase 7a adds a selectable larger recognizer
and audio diagnostics in response to real recognition failures. Complete and check one phase, then commit
its code, tests, documentation, and AI log together. Exclude environments,
downloaded models, recordings, and local logs. Phase 7 is evaluation; Phase 8 is
final documentation and delivery. Allowing pretrained ASR is settled; lecturer
acceptance of our separate manual-MFCC analysis branch is still pending.

## Sources

- Vosk model list and Apache-2.0 license for the selected model:
  https://alphacephei.com/vosk/models
- Vosk Python streaming API example (consulted for interface behavior):
  https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py
- Kaldi feature extraction background:
  https://kaldi-asr.org/doc/feat.html
- PowerPoint GotoSlide and current-slide read-back:
  https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowview.gotoslide
  https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowview.slide

The NumPy MFCC implementation, command grammar, application, and tests are
project code. Model accuracy must be evaluated on our own recordings.
