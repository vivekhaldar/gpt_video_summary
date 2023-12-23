#!/bin/bash
#
# First arg is URL of video

# If OPENAI_API_KEY is not set, exit.
if [ -z "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY is not set. Exiting."
    exit 1
fi

# Download video
video_url="$1"
echo $video_url
video_filename="$(youtube-dl --get-filename $video_url)"
extension="${video_filename##*.}"
filename="${video_filename%.*}"
simple_video_filename=$(echo "$filename" | tr '[:space:]' '_' | tr -dc '[:alnum:]_')
simple_video_filename="${simple_video_filename}.${extension}"
youtube-dl --download-archive ytdl_archive.txt -o $simple_video_filename $video_url
echo $simple_video_filename
echo "****** Downloaded video ******"

# Sometimes, youtube-dl will download a video with a different extension than mp4.
# Check if simple_video_filename exists, and if not, try to find it.
if [ ! -f "$simple_video_filename" ]; then
    echo "****** Could not find video file. Trying to find it... ******"
    # Get filename without extension.
    filename_no_ext="${simple_video_filename%.*}"
    echo $filename_no_ext
    # Find file with same filename, but different extension.
    simple_video_filename=$(find . -type f -iname "$filename_no_ext*" | head -1)
    echo $simple_video_filename
fi

# Transcribe video, with word-level timestamps
json_word_ts_filename="${simple_video_filename%.*}_wordts.json"
if [ ! -f "$json_word_ts_filename" ]; then
    python word_transcribe.py $simple_video_filename
fi
echo $json_word_ts_filename
echo "****** Transcribed video ******"

# Extract words from json file
words_filename="${simple_video_filename%.*}_words_only.json"
./get_all_words_in_sequence.sh $json_word_ts_filename $words_filename
echo "****** Extracted words from json file ******"

# Extract entire transcript (so we can summarize it)
full_transcript_filename="${simple_video_filename%.*}_full_transcript.txt"
jq '.text' $json_word_ts_filename  > $full_transcript_filename
echo $full_transcript_filename
echo "****** Extracted full transcript ******"

# Summarize video with GPT-4.
model_name="gpt-4-1106-preview"
summary_filename="${simple_video_filename%.*}_summary.txt"
# Check if summary file exists
if [ ! -f "$summary_filename" ]; then
    cat summarize-prompt.txt $full_transcript_filename | llm -m $model_name > $summary_filename
fi
echo $summary_filename
echo "****** Summarized transcript of video into direct quotes ******"

# Finally, create summarized video.
summary_video_filename="${simple_video_filename%.*}_summary.mp4"
if [ ! -f "$summary_video_filename" ]; then
    python sentence_times.py $words_filename $summary_filename $simple_video_filename $summary_video_filename $full_transcript_filename
fi
echo $summary_video_filename
echo "****** Created summarized video ******"

# Get duration of original video.
original_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $simple_video_filename)
summarized_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $summary_video_filename)
echo "Original duration: $original_duration"
echo "Summarized duration: $summarized_duration"
