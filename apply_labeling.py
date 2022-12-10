import os
import re
from argparse import ArgumentParser
from pydub import AudioSegment
from itertools import chain
from binaryornot.check import is_binary

from text_reformater import reformat
import label_auto_checker
from excel_tools import get_xlsx_contents


def apply_labeling(input_dir, output_dir, elms):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    elm_to_remove, elm_to_reverse, elm_to_merge, elm_to_par, elm_to_vas, elm_to_add_bracket = elms

    for file_num in elm_to_remove.keys():
        text_file_path = os.path.join(input_dir, file_num, 'transcript.txt')
        audio_dir_path = os.path.join(input_dir, file_num, 'audio')
        text_file_out_path = os.path.join(output_dir, file_num + '.cha')
        with open(text_file_path, mode='r', encoding='utf-8') as in_f:
            lines_to_remove = set(elm_to_remove[file_num])
            lines = in_f.readlines()
            line_audio_list = [[] for _ in range(len(lines))]
            line_time_list = ['' for _ in range(len(lines))]
            line_device_list = ['' for _ in range(len(lines))]
            for idx in range(len(lines)):
                lines[idx] = lines[idx].strip()
                # For removing space after *PAR/%xvas/%rep if it is a reply.
                # Need to check len(line_split) > 1 due to may be empty contents after %xvas
                line_split = lines[idx].split('\t', maxsplit=1)
                if len(line_split) > 1:
                    lines[idx] = line_split[0] + '\t' + line_split[1].strip()
            for idx in range(len(lines)):
                # Get audio info
                if '' in lines[idx]:
                    audio_find_list = re.findall('.*?', lines[idx])
                    assert len(audio_find_list) == 1
                    audio_path = audio_find_list[0].replace('', '')
                    line_audio_list[idx].append(audio_path)
                    lines[idx] = re.sub(r'[^]]+', '', lines[idx])
                    lines[idx] = lines[idx].strip()
                # Get time info
                if '{' in lines[idx]:
                    time_find_list = re.findall('\{.*?\}', lines[idx])
                    assert len(time_find_list) == 1
                    time_str = time_find_list[0]
                    line_time_list[idx] = time_str
                    lines[idx] = re.sub(r'\{[^]]+\}', '', lines[idx])
                    lines[idx] = lines[idx].strip()
                # Get device info
                if '~' in lines[idx]:
                    device_find_list = re.findall('~.*?~', lines[idx])
                    assert len(device_find_list) == 1
                    device_str = device_find_list[0]
                    line_device_list[idx] = device_str
                    lines[idx] = re.sub(r'~[^]]+~', '', lines[idx])
                    lines[idx] = lines[idx].strip()

            for par_idx in elm_to_add_bracket[file_num]:
                assert lines[par_idx].startswith('%rep')
                title, line_content = lines[par_idx].split('\t', maxsplit=1)
                audio_tag = ''
                if len(line_content.split('')) > 1:
                    audio_tag = '' + line_content.split('', maxsplit=1)[1]
                    line_content = line_content.split(' ', maxsplit=1)[0]
                if line_content.startswith('"') and line_content.endswith('"'):
                    line_content = line_content[1:]
                    line_content = line_content[:-1]
                lines[par_idx] = title + '\t' + '[*' + line_content + ']' + audio_tag

            for par_idx in elm_to_par[file_num]:
                line_content = lines[par_idx].split('\t', maxsplit=1)[1]
                if line_content.startswith('"') and line_content.endswith('"'):
                    line_content = line_content[1:]
                    line_content = line_content[:-1]
                lines[par_idx] = '*PAR:\t' + line_content

            for vas_idx in elm_to_vas[file_num]:
                line_content = lines[vas_idx].split('\t', maxsplit=1)[1]
                if line_content.startswith('"') and line_content.endswith('"'):
                    line_content = line_content[1:]
                    line_content = line_content[:-1]
                lines[vas_idx] = '%xvas:\t' + line_content

            # for unlabeled "%rep", replace to "*PAR" if it have audio, replace to "%xvas" if not
            for idx in range(len(lines)):
                if lines[idx].startswith('%rep'):
                    line_content = lines[idx].split('\t', maxsplit=1)[1]
                    if line_content.startswith('"') and line_content.endswith('"'):
                        line_content = line_content[1:]
                        line_content = line_content[:-1]
                    if len(line_audio_list[idx]) > 0:
                        lines[idx] = '*PAR:\t' + line_content
                    else:
                        lines[idx] = '%xvas:\t' + line_content

            for reverse_seg in elm_to_reverse[file_num]:
                lines[reverse_seg[0]:reverse_seg[1] + 1] = lines[reverse_seg[0]:reverse_seg[1] + 1][::-1]
                line_time_list[reverse_seg[0]:reverse_seg[1] + 1] = line_time_list[reverse_seg[0]:reverse_seg[1] + 1][
                                                                    ::-1]
                line_device_list[reverse_seg[0]:reverse_seg[1] + 1] = line_device_list[
                                                                      reverse_seg[0]:reverse_seg[1] + 1][::-1]
                line_audio_list[reverse_seg[0]:reverse_seg[1] + 1] = \
                    line_audio_list[reverse_seg[0]:reverse_seg[1] + 1][::-1]

            for merge_seg in elm_to_merge[file_num]:
                for idx in range(merge_seg[0], merge_seg[1]):
                    lines[merge_seg[0]] += ' ' + lines[idx + 1].split('\t', maxsplit=1)[1]
                    lines_to_remove.add(idx + 1)
                    lines[idx + 1] = ''
                    line_audio_list[merge_seg[0]].extend(line_audio_list[idx + 1])
                    line_audio_list[idx + 1].clear()

            # if comes a single alexa, and the next line is also PAR, then merge them automatically
            for idx in range(len(lines) - 1):
                if lines[idx] == '*PAR:\talexa' and lines[idx + 1].startswith('*PAR') and idx not in lines_to_remove \
                        and idx + 1 not in lines_to_remove:
                    lines[idx] += ' ' + lines[idx + 1].split('\t', maxsplit=1)[1]
                    lines_to_remove.add(idx + 1)
                    lines[idx + 1] = ''
                    line_audio_list[idx].extend(line_audio_list[idx + 1])
                    line_audio_list[idx + 1].clear()

            # if comes a %xvas/*PAR line with no content, remove that line
            for idx in range(len(lines)):
                if lines[idx] == '%xvas:':
                    lines_to_remove.add(idx)
                if lines[idx] == '*PAR:':
                    lines_to_remove.add(idx)

            # check audio files, remove them if corrupted (issue from amazon server).
            for line_idx, line_audio in enumerate(line_audio_list.copy()):
                for x in line_audio:
                    if not is_binary(os.path.join(audio_dir_path, x)):
                        line_audio_list[line_idx].remove(x)

            for index in sorted(list(lines_to_remove), reverse=True):
                del lines[index]
                del line_audio_list[index]
                del line_time_list[index]
                del line_device_list[index]

            assert len(lines) == len(line_audio_list) == len(line_time_list) == len(line_device_list)

            for idx in range(len(lines)):
                lines[idx] = reformat(lines[idx])

            # Make dirs in case the file_num is a path
            os.makedirs(os.path.dirname(os.path.join(output_dir, file_num)), exist_ok=True)

            audios = [[AudioSegment.from_wav(os.path.join(audio_dir_path, x)) for x in xx]
                      for xx in line_audio_list]
            audio_merge = sum(list(chain.from_iterable(audios)))
            audio_merge.export(os.path.join(output_dir, file_num + '.wav'), format="wav")

            audios_duration = [sum([x.duration_seconds * 1000 for x in xx])
                               for xx in audios]
            audio_start_time = 0.0
            for idx in range(len(lines)):
                # Put the time back
                lines[idx] += ' {}'.format(line_time_list[idx])

                # Put the device back
                lines[idx] += ' {}'.format(line_device_list[idx])

                # Align audio
                if audios_duration[idx] > 0:
                    audio_seg_end = audio_start_time + audios_duration[idx]
                    audio_align_label = ' ' + str(int(audio_start_time)) + '_' + \
                                        str(int(audio_seg_end)) + ''
                    audio_start_time = int(audio_seg_end)
                    lines[idx] = lines[idx] + audio_align_label

            print('Running auto label checking on {}.'.format(file_num))
            label_auto_checker.check(lines, file_num)

            text_list = ["@UTF8", '@Window:	228_525_408_680_2358_1_2862_1_2862_1',
                         "@Begin", "@Languages:\teng", "@Participants:\tPAR Participant, VAS Media",
                         "@ID:\teng|VAS|PAR|||||Participant|||",
                         "@ID:\teng|VAS|VAS|||||Media|||", '@Media: ' + file_num.split('/')[-1] + '.wav']
            lines = text_list + lines
            lines.append('@End')
            with open(text_file_out_path, mode='w', encoding='utf-8') as out_f:
                for idx in range(len(lines)):
                    out_f.write(lines[idx])
                    out_f.write('\n')


def main():
    ap = ArgumentParser()
    ap.add_argument(
        "--input_dir", required=False, default='vas_save',
        help="Directory of inputs."
    )
    ap.add_argument(
        "--output_dir", required=False, default='vas_final',
        help="Directory of outputs."
    )
    ap.add_argument(
        "--label_path", required=False, default='labels.xlsx',
        help="Path to label file (xlsx)."
    )
    args = vars(ap.parse_args())
    elms = get_xlsx_contents(args['label_path'])
    apply_labeling(args['input_dir'], args['output_dir'], elms)


if __name__ == '__main__':
    main()
