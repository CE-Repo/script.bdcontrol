"""Minimal stand-in for Kodi's xbmc module, used by tools/smoke_test.py."""
import json

LOGDEBUG = 0
LOGINFO = 1
LOGWARNING = 2
LOGERROR = 3
LOGFATAL = 4

LOGGED = []
BUILTINS = []
JSONRPC_RESPONSES = {}
INFO_LABELS = {
    'System.BuildVersion': '21.1 (21.1.0) Git:20240501-nexus',
    'System.FriendlyName': 'CoreELEC (Ugoos AM9 Pro)',
    'VideoPlayer.Title': 'Concert Disc',
    'Player.Process(videowidth)': '3840',
    'Player.Process(videoheight)': '2160',
}
COND_VISIBILITY = {
    'Player.HasVideo': True,
    'VideoPlayer.HasMenu': True,
    'VideoPlayer.IsInMenu': False,
    'System.HasMediaDVD': True,
}
PLAYING_FILE = 'bluray://udf%3a%2f%2f%2fdev%2fsr0%2f/BDMV/PLAYLIST/00800.mpls'


def log(message, level=LOGDEBUG):
    LOGGED.append((level, message))


def getInfoLabel(name):  # noqa: N802 - Kodi API name
    return INFO_LABELS.get(name, '')


def getCondVisibility(condition):  # noqa: N802
    return COND_VISIBILITY.get(condition, False)


def executebuiltin(builtin, wait=False):  # noqa: N802
    BUILTINS.append(builtin)


def executeJSONRPC(request):  # noqa: N802
    payload = json.loads(request)
    method = payload['method']
    if method in JSONRPC_RESPONSES:
        result = JSONRPC_RESPONSES[method]
        if callable(result):
            result = result(payload.get('params', {}))
        return json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': result})
    return json.dumps({'jsonrpc': '2.0', 'id': 1,
                       'error': {'code': -32601, 'message': 'not stubbed'}})


def sleep(milliseconds):
    pass


class Monitor(object):
    def abortRequested(self):  # noqa: N802
        return True

    def waitForAbort(self, timeout=0):  # noqa: N802
        return True

    def onSettingsChanged(self):  # noqa: N802
        pass


class Player(object):
    def isPlaying(self):  # noqa: N802
        return True

    def getPlayingFile(self):  # noqa: N802
        return PLAYING_FILE

    def getTime(self):  # noqa: N802
        return 120.0

    def getTotalTime(self):  # noqa: N802
        return 7200.0

    def pause(self):
        pass

    def stop(self):
        pass
