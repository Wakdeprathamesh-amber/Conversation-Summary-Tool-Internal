# Call Transcription Module

This module handles batch transcription of call audio files using AssemblyAI.

## Files
- `transcribe_calls.py`: Script to batch transcribe calls from a JSON list.
- `calls_to_transcribe.json`: Input file listing calls to transcribe (mobile number and audio URL).

## Usage
1. Ensure you have `assemblyai` installed and your API key set in the environment variable `ASSEMBLYAI_API_KEY`.
2. Place your input JSON in `calls_to_transcribe.json`.
3. Run the script:
   ```bash
   python transcribe_calls.py
   ```
4. Transcripts will be saved in the output directory as specified in the script. 