"""Minimal stand-in for Kodi's xbmcgui module."""

SELECT_RESULT = -1
NOTIFICATIONS = []
TEXTVIEWERS = []
PROPERTIES = {}


class Dialog(object):
    def notification(self, heading, message, icon=None, time=5000):
        NOTIFICATIONS.append((heading, message))

    def ok(self, heading, message):
        return True

    def yesno(self, heading, message):
        return False

    def select(self, heading, options, preselect=-1):
        return SELECT_RESULT

    def textviewer(self, heading, text, usemono=False):
        TEXTVIEWERS.append((heading, text))


class Window(object):
    def __init__(self, window_id=0):
        self.window_id = window_id

    def getProperty(self, name):  # noqa: N802
        return PROPERTIES.get(name, '')

    def setProperty(self, name, value):  # noqa: N802
        PROPERTIES[name] = value

    def clearProperty(self, name):  # noqa: N802
        PROPERTIES.pop(name, None)


class Control(object):
    def __init__(self):
        self.label = ''
        self.percent = 0.0

    def setLabel(self, label):  # noqa: N802
        self.label = label

    def setPercent(self, percent):  # noqa: N802
        self.percent = percent


class Action(object):
    def __init__(self, action_id=0, button_code=0):
        self._id = action_id
        self._code = button_code

    def getId(self):  # noqa: N802
        return self._id

    def getButtonCode(self):  # noqa: N802
        return self._code


class WindowXMLDialog(object):
    def __init__(self, *args, **kwargs):
        self._controls = {}

    def getControl(self, control_id):  # noqa: N802
        return self._controls.setdefault(control_id, Control())

    def doModal(self):  # noqa: N802
        pass

    def close(self):
        pass

    def setFocusId(self, control_id):  # noqa: N802
        pass
