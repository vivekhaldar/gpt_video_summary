# Get word-level timestamps for a video.

import stable_whisper
import os
import sys

# Models are: tiny, base, small, medium, large
MODEL = 'small'

def transcribe_video(filename):
    print('Loading model... ')
    model = stable_whisper.load_model(MODEL)

    # Construct output file names
    base_name = os.path.splitext(filename)[0]
    srt_file = base_name + '_wordts.srt'
    vtt_file = base_name + '_wordts.vtt'
    ass_file = base_name + '_wordts.ass'
    json_file = base_name + '_wordts.json'

    # Transcribe and save
    print('Transcribing... ')
    result = model.transcribe(filename)

    print('Saving... ')
    result.to_srt_vtt(srt_file)
    result.to_srt_vtt(vtt_file)
    result.to_ass(ass_file)
    result.save_as_json(json_file)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide the filename to transcribe as the first argument.")
    else:
        filename = sys.argv[1]
        transcribe_video(filename)
