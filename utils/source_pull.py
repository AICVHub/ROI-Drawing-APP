import cv2


def get_source(source_path):
    """
    pull source image or video
    """
    if source_path.startswith('videos:'):
        source = cv2.VideoCapture(source_path[7:].strip())
    elif source_path.startswith('images:'):
        print(source_path[7:])
        source = cv2.imread(source_path[7:].strip())
    else:
        assert False, 'source path error!'
    return source


def pull_source_frame(source):
    """
    pull source frame
    """
    if isinstance(source, cv2.VideoCapture):
        ret, frame = source.read()
    else:
        frame = source
        ret = True
    return ret, frame


def release_source(source):
    """
    release source
    """
    if isinstance(source, cv2.VideoCapture):
        source.release()
    else:
        pass


class SourcePuller:

    def __init__(self, source_path):
        self.source_path = source_path
        self.source = get_source(source_path)

    def pull_frame(self):
        return pull_source_frame(self.source)

    def release(self):
        release_source(self.source)
