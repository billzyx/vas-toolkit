# VAS toolkit

> A Voice Assistant System (VAS) data downloading & labeling tool (supporting Alexa).

## Quick guide

### Data downloading

1. Put your account and password in "config/example.yaml".
2. Set your date/time range for downloading in "config/example.yaml".
3. Run the program
```
$ python alexa.py --config_file_path "config/example.yaml"
```
4. Data will be at "vas_save/xxx". "xxx" is the datetime you initialize the downloading.

### Labeling

1. Open "labels.xlsx".
2. Put "xxx" at first column, second row (replacing "001").
3. Do labelling at the rest of the columns at the second row. The label can be empty.
4. Run the program
```
$ python apply_labeling.py
```
5. Result will be at "vas/final", using [CLAN](https://dali.talkbank.org/clan/) format. 
