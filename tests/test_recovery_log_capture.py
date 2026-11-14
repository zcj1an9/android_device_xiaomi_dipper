"""Exercise the recovery scripts with fake proc/sysfs; never use host pstore."""
from pathlib import Path
import os
import subprocess
import tarfile
import tempfile

SOURCE=Path(__file__).resolve().parents[1]/'recovery/root/system/bin'
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);base=root/'tmp';base.mkdir()
    pstore=root/'pstore';pstore.mkdir()
    params=root/'params';params.mkdir()
    proc=root/'proc';proc.mkdir()
    for name,value in [('cmdline','fixture cmdline'),('mounts','fixture mounts'),('uptime','1.0 1.0')]:
        (proc/name).write_text(value)
    for name,value in [('mem_address','2952790016'),('mem_size','4194304'),('record_size','262144'),('console_size','262144'),('pmsg_size','2097152'),('ftrace_size','262144')]:
        (params/name).write_text(value+'\n')
    saved=b'Previous Android kernel panic\n'
    original=pstore/'dmesg-ramoops-0';original.write_bytes(saved)
    env=dict(os.environ,RECOVERY_DIAG_BASE=str(base),RECOVERY_PSTORE_DIR=str(pstore),RECOVERY_RAMOOPS_PARAMS=str(params),RECOVERY_PROC_DIR=str(proc),RECOVERY_PSTORE_SAVER=str(SOURCE/'recovery-pstore-save.sh'))
    subprocess.run(['sh',str(SOURCE/'recovery-pstore-save.sh'),'post-fs'],env=env,check=True)
    output=base/'recovery-boot-logs'
    assert (output/'pstore-early/dmesg-ramoops-0').read_bytes()==saved
    assert original.read_bytes()==saved
    assert 'capture_stage=post-fs' in (output/'capture-info.txt').read_text()
    # A later collector must preserve the early snapshot even if pstore changes.
    original.write_bytes(b'changed after startup\n')
    subprocess.run(['sh',str(SOURCE/'recovery-logs.sh')],env=env,check=True,stdout=subprocess.DEVNULL)
    assert (output/'pstore-early/dmesg-ramoops-0').read_bytes()==saved
    assert (output/'pstore-current/dmesg-ramoops-0').read_bytes()==b'changed after startup\n'
    with tarfile.open(base/'recovery-boot-logs.tar.gz') as archive:
        names=archive.getnames()
        assert 'recovery-boot-logs/recovery-ramoops-params.txt' in names
        assert archive.extractfile('recovery-boot-logs/pstore-early/dmesg-ramoops-0').read()==saved
    # A device exposing no pstore records is normal and must still export metadata.
    original.unlink()
    empty=root/'empty';empty.mkdir();env['RECOVERY_DIAG_BASE']=str(empty)
    subprocess.run(['sh',str(SOURCE/'recovery-logs.sh')],env=env,check=True,stdout=subprocess.DEVNULL)
    assert (empty/'recovery-boot-logs/pstore-file-count.txt').read_text().strip()=='0'
    assert (empty/'recovery-boot-logs.tar.gz').is_file()
print('Early snapshot, preservation, parameter export, archive and empty-pstore tests passed')
