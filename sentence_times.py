# Given a phrase, find the start and end time
# of the phrase in the JSON file
#
# Arguments:
# 1. words-only timestamps JSON file
# 2. summary text file
# 3. original video file
# 4. output summary video file
import json
import string
import re
from moviepy.editor import VideoFileClip, concatenate_videoclips
from rapidfuzz import fuzz, process
import sys

# TODO: open issues
# 1. Summary contains phrase from a longer sentence.


# Normalize a string. This removes all punctuation, makes it lowercase and strips it.
def string_normalize(s):
    s = s.strip().lower()
    # Remove all punctuation
    s = s.translate(str.maketrans('', '', string.punctuation))
    # Replace multiple spaces with one space.
    s = ' '.join(s.split())
    return s

# Given file with full transcript, return a list of all sentences in the transcript.
def get_sentences(full_transcript_file):
    with open(full_transcript_file) as f:
        full_transcript = f.read()
    # Remove all punctuation except for periods, exclamation marks, and question marks.
    non_sentence_punctuation = string.punctuation.replace('.', '').replace('?', '').replace('!', '')
    full_transcript = full_transcript.translate(str.maketrans('', '', non_sentence_punctuation))
    # Replace multiple spaces with one space.
    full_transcript = ' '.join(full_transcript.split())
    # Split into sentences.
    sentences = re.split(r'(?<=[.!?])\s+', full_transcript)
    # Remove empty strings.
    sentences = list(filter(None, sentences))
    # Remove periods, exclamation marks, and question marks.
    sentences = [s.replace('.', '').replace('?', '').replace('!', '') for s in sentences]
    return sentences

def find_summary_phrase_times(summary_phrases, sentences_from_transcript, word_timestamp_json):
    THRESHOLD_SCORE = 80
    # Get start, end time for each phrase.
    start_end_list = []
    for phrase_to_search in summary_phrases:
        phrase_to_search = string_normalize(phrase_to_search)
        # This does fuzzy matching using rapidfuzz.
        _, score, matchidx = process.extractOne(phrase_to_search, sentences_from_transcript, scorer=fuzz.WRatio)
        if matchidx is None or score < THRESHOLD_SCORE:
            print(f'\n!!!! Could not find [{phrase_to_search}] in the video.\n')
            print(score)
            continue
        sentence_match = sentences_from_transcript[matchidx]
        print(f'## {phrase_to_search} -> {sentence_match}')
        start, end = find_phrase_time(sentence_match, word_timestamp_json)
        if (start, end) == (None, None):
            print(f'!! Could not find [{sentence_match}] in the video.\n')
        else:
            start_end_list.append((start, end))
            print(f'## {phrase_to_search} -> {sentence_match} -> {start} {end}')
    return start_end_list

def create_subclips(video_file, start_end_list, output_video_file):
    video = VideoFileClip(video_file)
    subclips = []
    for start, end in start_end_list:
        subclip = video.subclip(start, end)
        subclips.append(subclip)
    concatenated_clip = concatenate_videoclips(subclips)
    concatenated_clip.write_videofile(output_video_file)

def find_phrase_time(phrase, json_data):
    print(f'@@====== {phrase}')
    phrase = string_normalize(phrase)
    words = phrase.split()
    first_word = string_normalize(words[0])
    if len(words) == 0:
        return None, None
    for i in range(len(json_data)):
        current_word = string_normalize(json_data[i]['word'])
        # print(f'@@w [{current_word}] / [{first_word}]')
        if current_word == first_word:
            possible_match = ' '.join(word['word'] for word in json_data[i:i+len(words)])
            possible_match = string_normalize(possible_match)
            # print(f'@@m {possible_match}')
            if possible_match == phrase:
                print("FOUND EXACT MATCH")
                return json_data[i]['start'], json_data[i+len(words)-1]['end']
            else:
                # Let's see how close we came, then tweak a little.
                current_match_ratio = fuzz.ratio(phrase, possible_match)
                best_possible_match = possible_match
                best_match_ratio = current_match_ratio
                best_match_end = i+len(words)-1
                if (current_match_ratio > 90):
                    print("FOUND IT CLOSE ENOUGH {current_match_ratio}")
                    # Try adding one or two words.
                    for j in range(1, 3):
                        if i+len(words)+j >= len(json_data):
                            break
                        new_possible_match = ' '.join(word['word'] for word in json_data[i:i+len(words)+j])
                        new_possible_match = string_normalize(new_possible_match)
                        r = fuzz.ratio(phrase, new_possible_match)
                        print(f'@@mf {new_possible_match} {r}')
                        if r > best_match_ratio:
                            best_match_ratio = r
                            best_possible_match = new_possible_match
                            best_match_end = i+len(words)+j-1
                    if best_match_ratio > current_match_ratio:
                        print(f'IMPROVED BEST MATCH {best_possible_match} {best_match_ratio}')
                        return json_data[i]['start'], json_data[best_match_end]['end']
                # print("NOT FOUND. Going around again.")
    print("NOT FOUND AT ALL")
    return None, None

if __name__ == '__main__':

    # Load JSON data containing word timestamps.
    with open(sys.argv[1]) as f:
        word_timestamps = json.load(f)

    with open(sys.argv[2]) as f:
        summary_phrases = f.readlines()

    original_video_file = sys.argv[3]

    output_video_file = sys.argv[4]
    full_transcript_file = sys.argv[5]

    # Get start, end time for each phrase.
    start_end_list = find_summary_phrase_times(
        summary_phrases,
        get_sentences(full_transcript_file),
        word_timestamps)

    create_subclips(original_video_file, start_end_list, output_video_file)

