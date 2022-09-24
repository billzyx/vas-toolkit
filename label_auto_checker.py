import re

line_offset = 9
global_lines = []
global_file_num = ''


def show_warnings(idx, warnings_contents):
    print('Warning at file {}, line {}: {}'.format(global_file_num, idx + line_offset, warnings_contents))
    print('Line contents of the above warning: "{}"'.format(global_lines[idx]))


def check_par_audio(line_name_list, line_audio_list):
    for idx, (line_name, line_audio) in enumerate(zip(line_name_list, line_audio_list)):
        if line_name == '*PAR:' and line_audio is None:
            show_warnings(idx, '*PAR with no audio, check if it is a *PAR command.')


def check_vas_audio(line_name_list, line_audio_list):
    for idx, (line_name, line_audio) in enumerate(zip(line_name_list, line_audio_list)):
        if line_name == '%xvas:' and line_audio is not None:
            show_warnings(idx, '%xvas with audio, check if it is a %xvas command.')


def check_rep_star_label(line_content_list):
    error_list = [
        'audio could not be understood',
        'audio was not intended for this device',
        'audio was not intended for alexa',
    ]
    for idx, line_content in enumerate(line_content_list):
        if any(x in line_content.lower() for x in error_list):
            if '[*' not in line_content:
                show_warnings(idx, 'Alexa error appears, make sure to add [*].')


def prepare(lines):
    line_name_list = []
    line_content_list = []
    line_time_list = []
    line_audio_list = []
    for line in lines:
        line_split_name = line.split('\t', maxsplit=1)
        line_name_list.append(line_split_name[0])
        line_content = line_split_name[1]

        line_time = None
        if '{' in line_content:
            time_find_list = re.findall('\{.*?\}', line_content)
            assert len(time_find_list) == 1
            line_time = time_find_list[0]
            line_content = re.sub(r'\{[^]]+\}', '', line_content)
            line_content = line_content.strip()
        line_time_list.append(line_time)

        line_audio = None
        if '' in line_content:
            audio_find_list = re.findall('.*?', line_content)
            assert len(audio_find_list) == 1
            line_audio = audio_find_list[0].replace('', '')
            line_content = re.sub(r'[^]]+', '', line_content)
            line_content = line_content.strip()
        line_audio_list.append(line_audio)

        line_content_list.append(line_content)
    return line_name_list, line_content_list, line_time_list, line_audio_list


def check(lines, file_num):
    global global_lines
    global_lines = lines
    global global_file_num
    global_file_num = file_num
    line_name_list, line_content_list, line_time_list, line_audio_list = prepare(lines)

    check_par_audio(line_name_list, line_audio_list)
    check_vas_audio(line_name_list, line_audio_list)
    check_rep_star_label(line_content_list)
