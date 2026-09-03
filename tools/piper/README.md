# Piper TTS voices

AROUND THE MAIN uses Piper for local English TTS.

Primary voice:

    en_US-ryan-medium

Download the voice model with:

    python -m piper.download_voices en_US-ryan-medium \
      --data-dir tools/piper/voices

The model files are intentionally excluded from Git because they are large
binary assets and are downloaded locally when needed.

Current production voice:

    en_US-ryan-medium
