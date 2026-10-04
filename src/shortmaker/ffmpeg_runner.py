import logging
import os
import subprocess
import tempfile
import time
from threading import Event


class Cancelled(Exception):
    pass


class Runner:
    def __init__(self, cancel=None):
        self.cancel = cancel or Event()

    def check(self):
        if self.cancel.is_set():
            raise Cancelled("Renderização cancelada")

    def run(self, args, cwd=None, timeout=3600):
        self.check()
        logging.info("Executando %r", args)
        # Files avoid pipe deadlocks when FFmpeg emits long diagnostics.
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            try:
                process = subprocess.Popen([str(a) for a in args], cwd=cwd, stdout=stdout, stderr=stderr,
                                           stdin=subprocess.DEVNULL,
                                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            except OSError as exc:
                raise ValueError(f"Não foi possível iniciar {args[0]}: {exc}") from exc
            started = time.monotonic()
            try:
                while process.poll() is None:
                    self.check()
                    if time.monotonic() - started > timeout:
                        raise ValueError("Processo excedeu o tempo limite; consulte logs/shortmaker.log")
                    time.sleep(.1)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            self.check()
            stdout.seek(0)
            stderr.seek(0)
            output = stdout.read().decode("utf-8", errors="replace")
            error = stderr.read().decode("utf-8", errors="replace")
            if process.returncode:
                logging.error("Processo falhou: %s", error)
                tool = os.path.basename(str(args[0]))
                if tool.lower().startswith("python"):
                    raise ValueError("Processo de voz/transcrição falhou; consulte logs/shortmaker.log para detalhes")
                raise ValueError(f"Falha em {tool}: {error[-800:].strip()}")
            return output
