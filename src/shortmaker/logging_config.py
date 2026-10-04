import logging
from .paths import ROOT


def configure():
    folder = ROOT / "logs"
    folder.mkdir(exist_ok=True)
    logging.basicConfig(filename=folder / "shortmaker.log", encoding="utf-8", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
