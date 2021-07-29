# modified from https://github.com/hysmichael/srt_fcpxml_converter/blob/master/srt_converter.py


"""
SRT & FCPXML CONVERTER
REQUIREMENT: OpenCC (pip install opencc-python-reimplemented)
AUTHOR: MICHAEL HONG
"""

import xml.etree.ElementTree as ET
import re
import copy
import argparse
import os  # change

# change start
# parser = argparse.ArgumentParser(description="Convert between .srt and .fcpxml files for subtitles creation.")
# parser.add_argument('-i', '--input', required=True, help="name for the input file (.srt or .fcpxml)")
# parser.add_argument('-o', '--output', required=True, help="name for the ouput file (.srt or .fcpxml)")
# parser.add_argument('-c', '--convert', 
# 	help="(optional) to use OpenCC to convert between Simplified/Traditional Chinese. Please specify the OpenCC configurations (e.g., s2t, t2s)")
# parser.add_argument('-t', '--template', default='Template.xml',
# 	help="(optional) to use a user-specific template file to generate .fcpxml. Default to 'Template.xml'")
# parser.add_argument('-fr', '--framerate', default=29.97, type=float,
# 	help='(optional) framerate should be set in the template. This argument provides a sanity check. Default to 29.97fps')
# parser.add_argument('--offset', type=float,
# 	help='(optional) move the entire timeline forward/backward from input to output. In seconds')
# args = parser.parse_args()

# FILE_IN		 = args.input 
# FILE_OUT 	 = args.output
# XML_TEMPLATE = args.template
XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>

<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat1080p2997" frameDuration="1001/30000s" width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>
        <effect id="r2" name="Custom" uid=".../Titles.localized/Build In:Out.localized/Custom.localized/Custom.moti"/>
    </resources>
    <library>
        <event name="{EVENT_NAME}">
            <project name="{PROJECT_NAME}">
                <sequence format="r1" tcStart="0s" tcFormat="NDF">
                    <spine>
                        <title name="{TITLE_NO}" offset="{OFFSET}" ref="r2" duration="{DURATION}" start="{START}">
                            <param name="Position" key="9999/10199/10201/1/100/101" value="0 -418.279"/>
                            <param name="Alignment" key="9999/10199/10201/2/354/1002961760/401" value="1 (Center)"/>
                            <param name="Alignment" key="9999/10199/10201/2/373" value="0 (Left) 2 (Bottom)"/>
                            <param name="Out Sequencing" key="9999/10199/10201/4/10233/201/202" value="0 (To)"/>
                            <param name="Wrap Mode" key="9999/10199/10201/5/10203/21/25/5" value="1 (Repeat)"/>
                            <param name="Color" key="9999/10199/10201/5/10203/30/32" value="0 0 0"/>
                            <param name="Wrap Mode" key="9999/10199/10201/5/10203/30/34/5" value="1 (Repeat)"/>
                            <param name="Width" key="9999/10199/10201/5/10203/30/36" value="3"/>
                            <text>
                                <text-style ref="ts1">{TEXT}</text-style>
                            </text>
                            <text-style-def id="ts1">
                                <text-style font="Arial" fontSize="50" fontFace="Regular" fontColor="0.999996 1 1 1" shadowColor="0 0 0 0.75" shadowOffset="5 315" alignment="center"/>
                            </text-style-def>
                        </title>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>"""

cc = None
# if args.convert:
# 	from opencc import OpenCC
# 	cc = OpenCC(args.convert)
# change end

framerate_tuple = (1001, 30000) # default to 29.97fps

## TIME STAMP CONVERSION METHODS

def convert_xml_t(s, return_tuple=False):
	if '/' not in s:	# whole seconds
		return float(s[:-1])
	components = s.split('/')
	x = float(components[0])
	y = float(components[1][:-1])
	if return_tuple: ## convert to int
		return (int(components[0]), int(components[1][:-1]))
	return (x / y)

def convert_t_xml(t):
	multiplier, denominator = framerate_tuple
	x = int(int(int(t * denominator) / multiplier)) * multiplier
	if x % denominator == 0:
		return '%ds' % (x / denominator) ## whole number
	return f'{x}/{denominator}s'

def convert_t_srt(t):
	t_int = int(t)
	ms = int((t - t_int) * 1000)
	s = t_int % 60
	m = int(t_int / 60) % 60
	h = int(t_int / 3600)
	return f'{h:02}:{m:02}:{s:02},{ms:03}'

def convert_srt_t(arr):
	return float(arr[0]) * 3600. + float(arr[1]) * 60. + \
		float(arr[2]) + float(arr[3]) / 1000.

def convert_text(__str):
	if cc:
		return cc.convert(__str)
	return __str

################
# INPUT CONVERSTION METHODS

def process_input_srt():
	f = open(FILE_IN, 'r', encoding='utf-8-sig')
	lines = f.read().splitlines()
	total_rows = len(lines)

	i = 0
	data = []

	while i < total_rows:
		i += 1
		m = re.match('(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)', lines[i])
		t_start  = convert_srt_t(m.groups()[0:4])
		t_end    = convert_srt_t(m.groups()[4:8])
		data.append((t_start, t_end, lines[i + 1]))

		i += 3

	return data

def process_input_fcpxml():
	xml = ET.parse(FILE_IN)
	root = xml.getroot()
	n_library = root[1]
	n_event = n_library[0]
	n_project = n_event[0]
	n_sequence = n_project[0]
	n_spine = n_sequence[0]

	data = []
	for node in n_spine:
		if node.tag == 'title':

			n_text = node.find('text')[0].text
			if n_text == 'Title':
				continue # remove bad frames

			offset = convert_xml_t(node.get('offset')) 
			duration = convert_xml_t(node.get('duration'))
			end = offset + duration
			data.append((offset, end, n_text))

	return data

def process_output_srt(data):
	f = open(FILE_OUT, 'w')

	counter = 1
	for line in data:
		t_start, t_end, text = line
		f.write (f'{counter}\n')
		f.write (convert_t_srt(t_start) + ' --> ' + convert_t_srt(t_end) + '\n')
		f.write (convert_text(text) + '\n')
		f.write ('\n')
		counter += 1

	f.close()


def process_output_fcpxml(data):
	# change start
	# xml = ET.parse(XML_TEMPLATE) # change
	# root = xml.getroot()
	root = ET.fromstring(XML_TEMPLATE)
	# change end

	# check if template frameDuration is consistent with specified frame rate
	n_resources = root[0]

	xml_framerate = n_resources.find('format').get('frameDuration')
	xml_framerate_fps = 1 / convert_xml_t(xml_framerate)
	if abs(args.framerate - xml_framerate_fps) > 0.005:
        # change start
		global framerate_tuple
		framerate_tuple = (1001, round(args.framerate * 1001))
		# import pudb;pu.db
		xml_framerate = convert_t_xml(1/args.framerate)
		print('template framerate %.2ffps is inconsistent with specified framerate %.2ffps.\
		 Please set the correct framerate using flag -fr.' % (xml_framerate_fps, args.framerate))
		# change end

	# global framerate_tuple # change
	framerate_tuple = convert_xml_t(xml_framerate, return_tuple=True)

	# change start
	# change meta according to framerate
	n_resources.find('format').set('frameDuration', convert_t_xml(1/args.framerate)) # change
	n_resources.find('format').set('name', f'FFVideoFormat1080p{int(args.framerate*100)}')
	# change end

	n_library = root[1]
	n_event = n_library[0]
	n_event.set('name', 'CC_XML')
	n_project = n_event[0]
	n_project.set('name', event_name)

	n_sequence = n_project[0]
	n_spine = n_sequence[0]

	title_proto = n_spine.find('title') ## find the first title as template
	n_spine.append(ET.Element('divider')) ## add a divider between template and content

	counter = 1	
	for line in data:
		t_start, t_end, text = line

		# insert gap if not starting from 0s
		if counter == 1 and t_start > 0:
			gap_new = ET.Element('gap')
			gap_new.set('name', 'Gap')
			gap_new.set('offset', '0s')
			gap_new.set('duration', convert_t_xml(t_start))
			gap_new.set('start', '0s')
			n_spine.append(gap_new)

		title_new = copy.deepcopy(title_proto)

		offset   = convert_t_xml(t_start)
		duration = convert_t_xml(t_end - t_start)
		output_text = convert_text(text) # apply conversion


		title_new.set('name', '{%d} %s' % (counter, output_text))
		title_new.set('offset', offset)
		title_new.set('duration', duration)
		title_new.set('start', offset)

		title_new.find('text')[0].text = output_text
		title_new.find('text')[0].set('ref', 'ts%d' % (counter))
		title_new.find('text-style-def').set('id', 'ts%d' % (counter))

		n_spine.append(title_new)

		counter += 1
	
	while n_spine[0].tag != 'divider':
		n_spine.remove(n_spine[0])
	n_spine.remove(n_spine[0]) # remove divider

	f = open(FILE_OUT, 'w')
	f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	f.write('<!DOCTYPE fcpxml>\n')
	f.write('\n')
	# f.write(ET.tostring(root, encoding='UTF-8', xml_declaration=False).decode('utf-8')) # change
	f.write(ET.tostring(root, encoding='UTF-8').decode('utf-8')) # change
	f.close()


################

event_name = ''
# change start

# ## convert input file to internal representation
# if FILE_IN.endswith('.srt'):
# 	data = process_input_srt()
# 	event_name = FILE_IN[:-4]
# elif FILE_IN.endswith('.fcpxml'):
# 	data = process_input_fcpxml()
# 	event_name = FILE_IN[:-7]
# else:
# 	raise Exception('unsupported input file type: ' + FILE_IN)

# ## apply global offset (if applicable)
# if args.offset:
# 	data = list(map(lambda x: (x[0] + args.offset, x[1] + args.offset, x[2]), data))

# ## convert internal representation to output
# if FILE_OUT.endswith('.srt'):
# 	process_output_srt(data)
# elif FILE_OUT.endswith('.fcpxml'):
# 	process_output_fcpxml(data)
# else:
# 	raise Exception('unsupported output file type: ' + FILE_OUT)


def json_to_fcpxml(d, framerate=59.94, resolution='1920x1080'):
    assert resolution == '1920x1080'
    data = [(_['start'], _['end'], _['text']) for _ in d['subtitles']]
    global args
    args = type('', (), {})()
    args.framerate = framerate
    global FILE_OUT
    FILE_OUT = 'output.fcpxml'
    process_output_fcpxml(data)
    tmp = open('output.fcpxml', 'r').read()
    os.remove(FILE_OUT)
    return tmp
# change end