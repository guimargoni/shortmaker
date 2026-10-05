import json
import pytest
from shortmaker.editing_models import Effect, Editing, TrimPolicy
from shortmaker.editing import visual_filters, quality_warnings, edited_visual, validate_effects, trim_blank_edges
from shortmaker.models import Segment
from shortmaker.validation import parse_plan
from shortmaker.ass_builder import AssBuilder
from shortmaker.editing import add_text_cards


@pytest.mark.parametrize('effect', [
    {'type':'punch_in','at':1,'duration':.5,'scale':1.08},
    {'type':'slow_zoom','start_at':0,'end_at':2},
    {'type':'freeze_frame','at':1,'duration':.8},
    {'type':'text_card','at':1,'text':'Observe.'},
    {'type':'speed_change','start_at':0,'end_at':2,'speed':.85},
    {'type':'fade','at':0,'duration':.2},
    {'type':'hard_cut_marker','at':1},
])
def test_valid_effects(effect):
    segment = Segment(type='source_clip',start=0,end=4,effects=[effect])
    assert validate_effects(segment) > 0


@pytest.mark.parametrize('effect',[
    {'type':'punch_in','scale':.9}, {'type':'punch_in','duration':0},
    {'type':'speed_change','start_at':0,'end_at':1,'speed':.74},
    {'type':'speed_change','start_at':0,'end_at':1,'speed':1.36},
    {'type':'slow_zoom','start_at':2,'end_at':1},
    {'type':'freeze_frame','duration':1.3}, {'type':'fade','duration':.5},
    {'type':'text_card','text':''}, {'type':'shake'},
])
def test_invalid_effects(effect):
    with pytest.raises(ValueError):
        Effect(**effect)


@pytest.mark.parametrize('pace',['dramatic','normal','fast'])
def test_pace_and_trim_policy(pace):
    assert Editing(pace=pace).pace == pace
    assert TrimPolicy().preserve_dialogue and TrimPolicy().preserve_reaction
    with pytest.raises(ValueError):
        Editing(pace='random')
    with pytest.raises(ValueError):
        TrimPolicy(max_removal_ms=1000)
    slow = Segment(type='source_clip',start=0,end=8,effects=[{'type':'slow_zoom'}])
    validate_effects(slow,pace)
    assert slow.effects[0].end_at == {'dramatic':5,'normal':4,'fast':3}[pace]


def test_speed_duration_and_overlap_bounds():
    s=Segment(type='source_clip',start=0,end=4,effects=[{'type':'speed_change','start_at':1,'end_at':3,'speed':.8}])
    assert edited_visual(s) == pytest.approx(4.5)
    s.effects.append(Effect(type='speed_change',start_at=2,end_at=4))
    with pytest.raises(ValueError):
        validate_effects(s)


def test_marker_no_visual_and_text_card_safe_escape():
    assert visual_filters([Effect(type='hard_cut_marker',at=1)],30) == ''
    ass=AssBuilder()
    add_text_cards(ass,[Effect(type='text_card',text=r'{\pos(0,0)} Observe.',at=1)])
    assert r'{\pos(0,0)}' not in ass.events[0]
    assert ',8,60,60,285,' in ass.styles[0]


def test_legacy_and_quality_warnings():
    data={'schema_version':'1.1','shorts':[{'id':'x','timeline':[{'type':'source_clip','start':0,'end':14}]}]}
    plan=parse_plan(data)
    assert not plan.shorts[0].timeline[0].effects and not quality_warnings(plan.shorts[0])
    data['shorts'][0]['editing']={'editorial_quality_warnings':True}
    assert len(quality_warnings(parse_plan(data).shorts[0])) == 2
    data['shorts'][0]['timeline'][0]['effects']=[{'type':'freeze_frame','at':x,'duration':.3} for x in (1,2,3)]+[{'type':'punch_in','at':4,'scale':1.16},{'type':'text_card','at':6,'duration':3,'text':'Observe'}]
    warnings=' '.join(quality_warnings(parse_plan(data).shorts[0]))
    assert all(word in warnings for word in ('freeze','5s','1.15','2s'))


def test_trim_preserves_reactions_without_analysis(tmp_path):
    from types import SimpleNamespace
    s=Segment(type='source_clip',start=0,end=2,trim_policy={'remove_dead_time':True})
    assert trim_blank_edges('unused',s,tmp_path,0,None,None,SimpleNamespace(audio=True),'normal') is s


def test_real_effects_crossfade_and_freeze(tmp_path):
    from shortmaker.ffmpeg_runner import Runner
    from shortmaker.paths import executable
    from shortmaker.render_pipeline import Pipeline
    runner=Runner(); source=tmp_path/'source.mkv'
    runner.run([executable('ffmpeg'),'-y','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=12:duration=4','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=4','-c:v','ffv1','-c:a','pcm_s16le',source])
    effects=[{'type':'punch_in','at':.2,'duration':.4}, {'type':'slow_zoom','start_at':1,'end_at':2}, {'type':'freeze_frame','at':2.2,'duration':.6}, {'type':'speed_change','start_at':3,'end_at':4,'speed':.8}, {'type':'text_card','at':.9,'duration':.8,'text':'Observe.'}, {'type':'fade','at':0,'duration':.2}, {'type':'hard_cut_marker','at':2}]
    data={'schema_version':'1.1','defaults':{'video':{'preset':'ultrafast','fps_mode':'fixed','fps':12},'audio':{'normalize':False},'captions':{'enabled':False},'hook':{'enabled':False},'source_label':{'enabled':False}},'shorts':[
        {'id':'effects','timeline':[{'type':'source_clip','start':0,'end':4,'effects':effects,'reframe':{'mode':'manual_keyframes','keyframes':[{'at':0,'x':.2,'y':.5},{'at':4,'x':.8,'y':.5}]}}]},
        {'id':'cross','timeline':[{'type':'source_clip','start':0,'end':2,'transition_out':{'type':'crossfade','duration':.12}},{'type':'source_clip','start':2,'end':4}]},
    ]}
    outputs,failures=Pipeline().render(source,parse_plan(data),tmp_path/'out')
    assert not failures and len(outputs)==2
    info=json.loads(runner.run([executable('ffprobe'),'-v','error','-show_streams','-show_format','-of','json',outputs[0]]))
    assert (info['streams'][0]['width'],info['streams'][0]['height'])==(1080,1920)
    assert float(info['format']['duration']) == pytest.approx(4.25,abs=.15)
    # Video holds while source audio remains nonzero; compare decoded frozen frames.
    for i,at in enumerate((2.35,2.6)):
        runner.run([executable('ffmpeg'),'-y','-v','error','-ss',at,'-i',outputs[0],'-frames:v',1,'-f','rawvideo','-pix_fmt','rgb24',tmp_path/f'freeze{i}.raw'])
    import numpy as np
    a=np.fromfile(tmp_path/'freeze0.raw',dtype=np.uint8).astype(float)
    b=np.fromfile(tmp_path/'freeze1.raw',dtype=np.uint8).astype(float)
    assert abs(a-b).mean()<2
    audio=tmp_path/'pitch.wav'
    runner.run([executable('ffmpeg'),'-y','-v','error','-ss',3.3,'-t',.7,'-i',outputs[0],'-vn','-ar',48000,'-ac',1,'-c:a','pcm_s16le',audio])
    import wave
    with wave.open(str(audio),'rb') as wav:
        samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)
    peak=np.fft.rfftfreq(len(samples),1/48000)[np.abs(np.fft.rfft(samples)).argmax()]
    assert peak == pytest.approx(440,abs=5)  # atempo preserves pitch during 0.8x
    cross=json.loads(runner.run([executable('ffprobe'),'-v','error','-show_format','-of','json',outputs[1]]))
    assert float(cross['format']['duration']) == pytest.approx(3.88,abs=.2)


def test_real_blank_silent_edges_removal(tmp_path):
    from types import SimpleNamespace
    from shortmaker.ffmpeg_runner import Runner
    from shortmaker.paths import executable
    runner=Runner(); source=tmp_path/'blank.mkv'
    runner.run([executable('ffmpeg'),'-y','-v','error','-f','lavfi','-i','color=black:s=320x180:r=10:d=2','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t',2,'-c:v','ffv1','-c:a','pcm_s16le',source])
    s=Segment(type='source_clip',start=0,end=2,trim_policy={'remove_dead_time':True,'preserve_reaction':False,'max_removal_ms':300})
    cut=trim_blank_edges(source,s,tmp_path,0,runner,executable('ffmpeg'),SimpleNamespace(audio=True),'normal')
    assert cut.start==pytest.approx(.3) and cut.end==pytest.approx(1.7)
    class FailedAnalysis:
        def check(self): pass
        def run(self,args): raise ValueError('analysis unavailable')
    assert trim_blank_edges(source,s,tmp_path,2,FailedAnalysis(),executable('ffmpeg'),SimpleNamespace(audio=True),'normal') is s


@pytest.mark.parametrize('mode',['continue','duck','mute'])
def test_freeze_source_audio_modes(tmp_path,mode):
    import wave
    import numpy as np
    from types import SimpleNamespace
    from shortmaker.ffmpeg_runner import Runner
    from shortmaker.paths import executable
    from shortmaker.editing import prepare_clip
    runner=Runner(); source=tmp_path/'tone.mkv'
    runner.run([executable('ffmpeg'),'-y','-v','error','-f','lavfi','-i','color=black:s=320x180:r=10:d=2','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2','-c:v','ffv1','-c:a','pcm_s16le',source])
    # Even black frames are retained when any nonzero audio could be dialogue.
    seg=Segment(type='source_clip',start=0,end=2,trim_policy={'remove_dead_time':True,'preserve_reaction':False,'max_removal_ms':300})
    assert trim_blank_edges(source,seg,tmp_path,0,runner,executable('ffmpeg'),SimpleNamespace(audio=True),'normal').start == 0
    seg.effects=[Effect(type='freeze_frame',at=.5,duration=.6,audio_mode=mode)]
    dest,_=prepare_clip(source,seg,tmp_path,1,runner,executable('ffmpeg'),SimpleNamespace(audio=True,fps=10),'normal')
    wavpath=tmp_path/'audio.wav'
    runner.run([executable('ffmpeg'),'-y','-v','error','-i',dest,'-vn','-ac',1,'-c:a','pcm_s16le',wavpath])
    with wave.open(str(wavpath),'rb') as wav:
        pcm=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)
    rms=lambda a: np.sqrt(np.mean(a*a))
    ratio=rms(pcm[round(.65*48000):round(.9*48000)])/rms(pcm[:round(.3*48000)])
    assert ratio == pytest.approx({'continue':1,'duck':.158489,'mute':0}[mode],abs=.01)


def test_crossfade_bounds():
    with pytest.raises(ValueError):
        parse_plan({'schema_version':'1.1','shorts':[{'id':'x','timeline':[{'type':'source_clip','start':0,'end':2,'transition_out':{'type':'crossfade','duration':.5}}]}]})
