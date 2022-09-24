import os


class FileSaver:
    # Audios: root_dir/audio_dir_name/001.wav, root_dir/audio_dir_name/002.wav ...
    # Texts: root_dir/text_file_name.txt
    def __init__(self, root_dir, audio_dir_name='audio', text_file_name='transcript', save_date_time=False,
                 save_device_name=False):
        self.root_dir = root_dir
        self.audio_dir = os.path.join(root_dir, audio_dir_name)
        self.text_file_path = os.path.join(root_dir, text_file_name + '.txt')
        self.audio_file_count = 1
        self.text_lines = []
        self.save_date_time = save_date_time
        self.box_time = None
        self.save_device_name = save_device_name
        self.device_name = None
        os.makedirs(self.audio_dir)

    def add_audio(self, wav_binary):
        with open(os.path.join(self.audio_dir, '{:03d}.wav'.format(self.audio_file_count)), 'wb') as f:
            f.write(wav_binary)
        self.audio_file_count += 1

    def set_box_time(self, box_time):
        self.box_time = box_time

    def set_device_name(self, device_name):
        self.device_name = device_name

    def add_info(self, text_line):
        if self.save_date_time:
            text_line = '{} {{{}}}'.format(text_line, self.box_time)
        if self.save_device_name:
            text_line = '{} ~{}~'.format(text_line, self.device_name)
        return text_line

    def add_text(self, text_line):
        text_line = self.add_info(text_line)
        self.text_lines.append(text_line)

    def add_text_with_audio_link(self, text_line):
        text_line = self.add_info(text_line)
        text_line = '{} {:03d}.wav'.format(text_line, self.audio_file_count)
        self.text_lines.append(text_line)

    def end_of_add(self):
        with open(self.text_file_path, 'w') as f:
            for line in self.text_lines:
                f.write(line)
                f.write("\n")
