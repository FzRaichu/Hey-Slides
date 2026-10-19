# Controlled English recording for the next recognition comparison

This is a proposed reading script, not a recording or a measured result.
The small.en experiment used English-only recognition. An Indonesian or mixed
language presentation requires a separate multilingual comparison.

## Setup

Restart the desktop application. Choose Demo slides, Light English, Direct
commands, Command assist, and Record input for diagnosis. Click Start listening.
Use Go to slide three here because the built-in demo has only five slides.

## Read once, in this order

Read the paragraph naturally. Do not read the instructions or section titles:

> Today I am presenting our speech recognition project. The application listens
> to the microphone and converts speech into text. We extract audio features
> manually and use a pretrained model for recognition. This sentence explains
> the system and should not move any slides.

Then say each command once, with about two seconds of silence after it:

> Next slides.

> Previous slides.

> Go to slide three.

Then read these sentences, which should not cause navigation:

> The next slide contains our evaluation results.

> Do not go to slide four.

Click Stop. Keep the WAV and session log. If you skip, repeat, or change words,
note the actual wording; the printed script must not automatically be treated
as a confirmed reference. Avoid playing the WAV while listening is active.

## Expected actions

Starting from demo slide one: Next -> 2; Previous -> 1; Go to slide three -> 3.
The paragraph and last two sentences should produce no actions. Judge this
using the voice action log, not a text-only parser test.

This recording can establish a baseline for ordinary-speech WER and direct
commands on the same audio. It is still one speaker and one setting; retain
later recordings as fresh test data rather than tuning on every sample.
