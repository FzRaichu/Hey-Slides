"""Compare free transcription and focused command decoding on the SAME audio.

No microphone, speaker playback, or presentation actions. File EOF may finalize
a candidate; this is a recognition comparison, not live latency measurement.
"""

import argparse
import json
from pathlib import Path
import wave

from app import config
from app.command_recognition import CommandRecognizer, align_command_endpoint
from app.commands import CommandParser
from app.recognition import StreamingRecognizer, load_model


def compare(path, profile="light", model=None):
    model = load_model(config.model_path(profile)) if model is None else model
    decoders = {"unrestricted": StreamingRecognizer(model), "command_focused": CommandRecognizer(model)}
    parsers = {name: CommandParser() for name in decoders}
    output = {name: [] for name in decoders}
    samples = 0

    def collect(name, event, eof=False):
        if event["kind"] != "final" or not event["text"]:
            return
        eligible = event.get("eligible", True)
        if eligible:
            decision = parsers[name].accept(event["text"], str(len(output[name])), now=samples / 16000)
            action, target, status = decision.action, decision.target_slide, decision.status
        else:
            parsers[name].disarm()
            action, target, status = None, None, event["reason"]
        output[name].append({"text": event["text"], "eligible": eligible, "status": status,
                             "proposed_action": action, "target_slide": target,
                             "words": event["words"], "mean_score": event.get("mean_score"),
                             "audio_processed_seconds": samples / 16000,
                             "finalized_at_eof": eof})

    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
            raise ValueError("Expected mono 16 kHz signed PCM16 WAV")
        while data := wav.readframes(config.AUDIO_BLOCK_SAMPLES):
            samples += len(data) // 2
            general = decoders["unrestricted"].feed(data)
            focused = decoders["command_focused"].feed(data)
            focused = align_command_endpoint(general, focused, decoders["command_focused"])
            collect("unrestricted", general)
            collect("command_focused", focused)
        for name, decoder in decoders.items():
            collect(name, decoder.finish(), eof=True)
    return {"source": str(Path(path).resolve()), "model_profile": profile,
            "audio_seconds": samples / 16000, "results": output,
            "note": "Offline comparison only. Focused scores are not calibrated; proposed actions were not executed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--profile", choices=config.MODEL_PROFILES, default="light")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.wav, args.profile)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
