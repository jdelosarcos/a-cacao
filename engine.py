"""Lazy execution adapter preserving original analysis modules and their dependencies."""
import ast, contextlib, io, os, re, tempfile, hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SOURCE = Path(__file__).with_name('original_analysis.py')
TEXT = SOURCE.read_text(encoding='utf-8')
MARKERS = [(int(m.group(1)), m.start()) for m in re.finditer(r'(?m)^# MODULE (\d+)\s*[—–-]', TEXT)]
BLOCKS = {}
for i, (num, pos) in enumerate(MARKERS):
    end = MARKERS[i+1][1] if i+1 < len(MARKERS) else len(TEXT)
    BLOCKS[num] = TEXT[pos:end]

class AnalysisSession:
    def __init__(self, data: bytes):
        self.root = Path(tempfile.mkdtemp(prefix='cacao_streamlit_'))
        self.data = self.root/'CacaoY.csv'
        self.data.write_bytes(data)
        self.output = self.root/'results'
        self.ns = {'__name__':'__main__'}
        self.completed = set()
        self.logs = {}
        self.key = hashlib.sha256(data).hexdigest()

    def run(self, module):
        if module in self.completed:
            return
        if module == 1:
            dependencies=[]
        elif module == 8:
            dependencies=[1]  # Forecasting can run without the survey analysis pipeline
        elif module <= 7:
            dependencies=list(range(1,module))
        elif module in (9,10,11):
            dependencies=list(range(1,module))
        else:
            raise ValueError('Supported computational modules are 1 through 11.')
        for dep in dependencies:
            self.run(dep)
        if module == 1:
            os.environ['CACAO_DATA']=str(self.data)
            os.environ['CACAO_OUTPUT']=str(self.output)
            os.environ['CACAO_TIME_SERIES']=str(self.root/'not_uploaded.csv')
        # Prevent the notebook's plot display from creating UI output.
        buffer=io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            exec(compile(BLOCKS[module], str(SOURCE), 'exec'), self.ns)
        plt.close('all')
        self.logs[module]=buffer.getvalue()
        self.completed.add(module)

    def csv(self, filename):
        import pandas as pd
        path=self.output/filename
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
