import sys
import json
import os

file_path = sys.argv[1]
json_file = json.load(open(file_path, 'r'))

texts = json_file['materials']['texts']

id_to_text = {}
for caption in texts:
    id_to_text[caption['id']] = caption['content']


# 9166666 = 9.1 s
tracks = []
for track in json_file['tracks']:
    if track['type'] == 'text':
        for segment in track['segments']:
            material_id = segment['material_id']
            text = id_to_text[material_id]
            start = segment['target_timerange']['start']
            duration = segment['target_timerange']['duration']
            tracks.append({
                'text': text,
                'start': start,
                'duration': duration
            })
print(tracks)

out_json = {}
out_json['subtitles'] = []
for track in tracks:
    out_json['subtitles'].append({
        'text': track['text'],
        'start': track['start'] // 1000, # in json 9100=9.1
        'end': (track['start'] + track['duration']) // 1000
    })
json.dump(out_json, open(f'/Users/ruotianluo/Downloads/{os.path.basename(file_path)}', 'w'))


from to_fcpxml import json_to_fcpxml
open(f'/Users/ruotianluo/Downloads/{os.path.splitext(os.path.basename(file_path))[0]}'+'.fcpxml', 'w').write(json_to_fcpxml(out_json))


# # convert srt file to fcpxml file
# def srt_to_fcpxml(