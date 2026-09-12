# -*- coding: utf-8 -*-
"""Static lookup tables, keyed on the lowercase codec id Kodi returns.

The codec ids are the decoder's own short names, which is why a track arrives
as "truehd_atmos" rather than as anything a viewer would recognise. The
spellings here follow script.tinyppi's tables, which were collected against
real discs; the guessed variants are kept alongside them so a disc that uses
either spelling still resolves.
"""

# An object-audio format is split into its bed format and the extension
# carried above it, so the extension can follow the channel layout:
# "Dolby TrueHD 7.1 (Atmos)". Everything else is a plain name.
AUDIO_CODEC_MAP = {
    # AAC
    'aac': 'AAC',
    'aac_latm': 'AAC',
    'aac_lc': 'AAC-LC',
    'aac_ltp': 'AAC-LTP',
    'aac_ssr': 'AAC-SSR',
    'he_aac': 'HE-AAC',
    'he_aac_v2': 'HE-AAC v2',

    # Dolby
    'ac3': 'Dolby Digital',
    'dolbydigital': 'Dolby Digital',
    'eac3': 'Dolby Digital Plus',
    'eac3_ddp_atmos': ('Dolby Digital Plus', 'Atmos'),
    'eac3_atmos': ('Dolby Digital Plus', 'Atmos'),
    'truehd': 'Dolby TrueHD',
    'truehd_atmos': ('Dolby TrueHD', 'Atmos'),

    # DTS
    'dca': 'DTS',
    'dts': 'DTS',
    'dts_96_24': 'DTS 96/24',
    'dts_es': 'DTS-ES',
    'dts_express': 'DTS Express',
    'dtsexpress': 'DTS Express',
    'dtshd': 'DTS-HD',
    'dtshd_hra': 'DTS-HD HRA',
    'dtshd_ma': 'DTS-HD MA',
    'dtshd_ma_x': ('DTS-HD MA', 'DTS:X'),
    'dtshd_ma_x_imax': ('DTS-HD MA', 'DTS:X IMAX'),
    'dtshd_ma_imax': ('DTS-HD MA', 'DTS:X IMAX'),

    # Lossless / PCM
    'alac': 'ALAC',
    'flac': 'FLAC',
    'lpcm': 'LPCM',
    'pcm': 'PCM',
    'pcm_bluray': 'LPCM',
    'pcm_s16le': 'PCM',
    'pcm_s24le': 'PCM',
    'wav': 'WAV',
    'wavpack': 'WavPack',

    # Compressed
    'ape': "Monkey's Audio (APE)",
    'mp1': 'MP1',
    'mp2': 'MP2',
    'mp3': 'MP3',
    'mp3float': 'MP3',
    'ogg': 'Ogg Vorbis',
    'opus': 'Opus',
    'vorbis': 'Vorbis',
    'wmapro': 'WMA Pro',
    'wmav2': 'WMA',

    # Misc
    'aif': 'AIFF',
    'aifc': 'AIFF-C',
    'aiff': 'AIFF',
    'avc': 'AVC',
    'cdda': 'CD Audio',
}

SUBTITLE_CODEC_MAP = {
    'ass': 'ASS',
    'dvb_subtitle': 'DVB-SUB',
    'dvb_teletext': 'DVB-Text',
    'dvd_subtitle': 'VobSub',
    'dvdsub': 'VobSub',
    'hdmv_pgs_subtitle': 'PGS',
    'pgs': 'PGS',
    'microdvd': 'MicroDVD',
    'mov_text': 'Timed Text',
    'mpl2': 'MPL2',
    'realtext': 'RealText',
    'sami': 'SAMI',
    'srt': 'SubRip',
    'ssa': 'SSA',
    'subrip': 'SubRip',
    'text': 'Text',
    'ttml': 'TTML',
    'vplayer': 'VPlayer',
    'webvtt': 'WebVTT',
    'xsub': 'XSUB',
}

# Channel count -> surround layout.
CHANNELS_MAP = {
    1: '1.0',
    2: '2.0',
    3: '2.1',
    4: '4.0',
    5: '5.0',
    6: '5.1',
    7: '6.1',
    8: '7.1',
    10: '9.1',
}
