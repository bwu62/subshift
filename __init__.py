from .subshift import Subtitle
import glob

def listSrts():
    return glob.glob("./*.srt")
