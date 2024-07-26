# GNU AFFERO GENERAL PUBLIC LICENSE v3.0 (see LICENSE or https://www.gnu.org/licenses/agpl-3.0.txt)

import pysrt, sys, getopt, numbers, genanki, random, tempfile, shutil, traceback, datetime, subprocess, multiprocessing, html
from pathlib import Path
from tqdm import tqdm
from subprocess import Popen, PIPE

TrackA = 0
TrackB = 0
Media = ""
CJK = "none"
Encoding = "iso-8859-1"
Title = "Unknown Title"

TMP = tempfile.mkdtemp()+"/"
#TMP = "TMP/"

AnkiModel = genanki.Model(random.randrange(1 << 30, 1 << 31),
                         'Video2Anki With Media',
                         fields = [{'name' : 'Question'},
                                   {'name' : 'Answer'},
                                   {'name' : 'Voiceline'}],
                         templates = [{'name' : 'Card',
                                       'qfmt' : '{{Question}}<br><{{Voiceline}}',
                                       'afmt' : '{{FrontSide}}<hr id="answer">{{Answer}}'}])

def parse_args():
    opt = "m:a:b:c:e:t:"
    lopt = ["media-file=", "track-a=", "track-b=", "cjk-mode=", "encoding=", "title="]
    args, vals = getopt.getopt(sys.argv[1:], opt, lopt)
    try:
        for arg, val in args:
            print("<"+arg+"> -> "+val)
            if arg in ("-m", "--media-file"):
                global Media
                Media = val
                print("media set to ", Media)
            elif arg in ("-a", "--track-a"):
                global TrackA
                TrackA = val
            elif arg in ("-b", "--track-b"):
                global TrackB
                TrackB = val
            elif arg in ("-e", "--encoding"):
                global Encoding
                Encoding = val
            elif arg in ("-t", "--title"):
                global Title
                Title = val
            elif arg in ("-c", "--cjk-mode"):
                if val in ("c", "j", "k"):
                    global CJK
                    CJK = val
                else:
                    raise Exception('invalid cjk value: ', val)
    except getopt.error as err:
        print(str(err))

def to_seconds(t):
    s = t.hour*60*60 + t.minute*60 + t.second
    m = int(t.microsecond/1000)
    return str(s)+'.'+str(m)[0]

def to_duration(start, end):
    t = start
    sa = t.hour*60*60 + t.minute*60 + t.second
    ma = int(t.microsecond/1000)
    t = end
    se = t.hour*60*60 + t.minute*60 + t.second
    me = int(t.microsecond/1000)
    s = se-sa
    m = me-ma
    if m < 0:
        s = s - 1
        m = 1000-m
    return str(s)+'.'+str(m)[0]

def extract_audio(name, start, end):
    cmds = ["ffmpeg", "-y", "-threads", str(multiprocessing.cpu_count()), "-i", Media, "-ss", to_seconds(start), "-t", to_duration(start, end), name]
    cmd = ""
    for c in cmds:
        cmd = cmd + str(c) + " "
    subprocess.check_call(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          shell=True)

def extract_track(idx):
    cmds = ["ffmpeg", "-i", Media, "-map=0:s:"+str(idx), TMP+Media+"_"+str(idx)+".srt"]
    cmd = ""
    for c in cmds:
        cmd = cmd + str(c) + " "
    subprocess.check_call(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          shell=True)
    return TMP+Media+"_"+idx+".srt"

def get_track(track):
    if isinstance(track, numbers.Number):
        track = extract_srt(track)
    return pysrt.open(track)

def overlaps(start_a, end_a, start_b, end_b):
    start_c = start_b if start_a < start_b else start_a
    end_c = end_b if end_a > end_b else end_b
    return start_c < end_c

def apply_cjk(original):
    text = ""
    lookup = ""
    if CJK=="c":
        lookup = "https://strokeorder.com/chinese/"
    elif CJK=="j":
        lookup = "https://japandict.com/kanji/"
    elif CJK=="k":
        lookup = "https://koreanhanja.app/"
    else:
        return html.escape(original)
    for p in original:
        escaped_p = html.escape(p)
        if is_cjk(p) and lookup!="":
            text = text + "<a href=\"" + lookup + escaped_p + "\">" + escaped_p + "</a>"
        else:
            text = text + escaped_p
    return text

def is_cjk(p):
    cjk_ranges = [
        ( 0x4E00,  0x62FF),
        ( 0x6300,  0x77FF),
        ( 0x7800,  0x8CFF),
        ( 0x8D00,  0x9FCC),
        ( 0x3400,  0x4DB5),
        (0x20000, 0x215FF),
        (0x21600, 0x230FF),
        (0x23100, 0x245FF),
        (0x24600, 0x260FF),
        (0x26100, 0x275FF),
        (0x27600, 0x290FF),
        (0x29100, 0x2A6DF),
        (0x2A700, 0x2B734),
        (0x2B740, 0x2B81D),
        (0x2B820, 0x2CEAF),
        (0x2CEB0, 0x2EBEF),
        (0x2F800, 0x2FA1F)
    ]
    cp = ord(p)
    for bottom, top in cjk_ranges:
        if cp >= bottom and cp <= top:
            return True
    return False

def match_tracks(a, b):
    matched = []
    media = []
    matchbar = tqdm(total=len(a) if len(a) > len(b) else len(b))
    for sub_a in a:
        start_a = sub_a.start.to_time()
        end_a = sub_a.end.to_time()
        for sub_b in b:
            start_b = sub_b.start.to_time()
            end_b = sub_b.end.to_time()
            if start_b > end_a:
                # skip a, b is past a
                break
            if end_b < start_a:
                # skip b, a is past b
                matchbar.update(1)
                continue
            elif overlaps(start_a, end_a, start_b, end_b):
                # match
                audio_name = str(len(matched)) + ".opus"
                media.append(TMP + audio_name)
                extract_audio(TMP + audio_name, start_a, end_a)
                text_b = apply_cjk(html.escape(sub_b.text))
                matched.append(genanki.Note(model=AnkiModel, fields=[text_b, html.escape(sub_a.text), "[sound:"+audio_name+"]"]))
        matchbar.update(1)
    matchbar.close()
    return matched, media

try:
    parse_args()
    if Path(Media).is_file()==False:
        raise Exception('file <', Media, '> does not exist')
    global AnkiDeck
    AnkiDeck = genanki.Deck(random.randrange(1 << 30, 1 << 31),Title)
    subs_a = get_track(TrackA)
    subs_b = get_track(TrackB)
    print("matching subtitles of both tracks...")
    notes, media = match_tracks(subs_a, subs_b)
    for note in notes:
        AnkiDeck.add_note(note)
    print("generating anki deck")
    package = genanki.Package(AnkiDeck)
    package.media_files = media
    print("writing apkg file...")
    package.write_to_file(Title+".apkg")
    print("done")
except Exception as e:
    print(traceback.format_exc())
except subprocess.CalledProcessError as e:
    print(e.output)

shutil.rmtree(TMP)
