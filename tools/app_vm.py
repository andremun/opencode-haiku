#!/usr/bin/env python3
"""Isolated cardless QEMU application VM. Never accepts extra QEMU arguments."""
import argparse, hashlib, json, os, shutil, socket, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VM=ROOT/'vm'; ISO=ROOT/'cache/haiku-master-hrev60207-x86_64-anyboot.iso'
SOCKET=Path('/tmp/haiku-app-'+hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]+'.sock')
EXPECTED='4cd0765e078414681cd64b1063f5d6c0d19dc6daa51c142c544cc4d614260e35'
PLAIN={' ':'spc','-':'minus','=':'equal','.':'dot',',':'comma','/':'slash',';':'semicolon',"'":'apostrophe','[':'bracket_left',']':'bracket_right','\\':'backslash','`':'grave_accent'}
SHIFT={'_':'minus','+':'equal','>':'dot','<':'comma','?':'slash',':':'semicolon','"':'apostrophe','{':'bracket_left','}':'bracket_right','|':'backslash','~':'grave_accent','!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0'}
def monitor(command):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5);s.connect(str(SOCKET))
        data=b''
        while b'(qemu)' not in data:
            chunk=s.recv(65536)
            if not chunk:raise RuntimeError('QEMU closed before monitor greeting')
            data+=chunk
        s.sendall((command+'\n').encode());data=b''
        while b'(qemu)' not in data:
            chunk=s.recv(65536)
            if not chunk:break
            data+=chunk
        return data.decode(errors='replace')
def key(c):
    if c.isascii() and (c.islower() or c.isdigit()):return c
    if c.isascii() and c.isupper():return 'shift-'+c.lower()
    if c in PLAIN:return PLAIN[c]
    if c in SHIFT:return 'shift-'+SHIFT[c]
    raise ValueError('Unsupported keyboard character: '+repr(c))
def type_line(text, submit=True):
    for c in text:
        monitor('sendkey '+key(c)+' 20');time.sleep(.045)
    if submit:
        monitor('sendkey ret');time.sleep(.15)
def start(installed,memory_mib,kvm=False):
    VM.mkdir(exist_ok=True)
    if (SOCKET).exists():
        try:monitor('info status')
        except OSError:(SOCKET).unlink()
        else:raise SystemExit('This application VM is already running')
    if hashlib.sha256(ISO.read_bytes()).hexdigest()!=EXPECTED:raise SystemExit('ISO checksum mismatch')
    disk=VM/'system.qcow2'
    if not disk.exists():subprocess.run(['qemu-img','create','-f','qcow2',str(disk),'32G'],check=True)
    if not (VM/'vars.fd').exists():shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd',VM/'vars.fd')
    args=['qemu-system-x86_64','-name','haiku-app','-machine','q35',*(['-accel','kvm','-cpu','host'] if kvm else ['-accel','tcg,thread=multi','-cpu','qemu64']),'-smp','2','-m',str(memory_mib),'-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd','-drive','if=pflash,format=raw,file='+str(VM/'vars.fd'),'-drive','file='+str(disk)+',format=qcow2,if=none,id=system','-device','ide-hd,drive=system,bus=ide.0'+(',bootindex=1' if installed else ''),'-device','qemu-xhci','-device','usb-tablet','-qmp','unix:'+str(SOCKET)+'.qmp,server,nowait','-vga','std','-netdev','user,id=n0,hostfwd=tcp:127.0.0.1:2233-:22','-device','e1000,netdev=n0','-display','none','-serial','file:'+str(VM/'serial.log'),'-monitor','unix:'+str(SOCKET)+',server,nowait']
    if not installed:
        boot=VM/'boot.qcow2'
        if not boot.exists():subprocess.run(['qemu-img','create','-f','qcow2','-F','raw','-b',str(ISO),str(boot)],check=True)
        args+=['-drive','file='+str(boot)+',format=qcow2,if=none,id=install','-device','ide-hd,drive=install,bus=ide.1,bootindex=1']
    log=(VM/'qemu.out').open('wb');p=subprocess.Popen(args,stdout=log,stderr=log,start_new_session=True)
    time.sleep(1)
    if p.poll() is not None:raise SystemExit((VM/'qemu.out').read_text())
    (VM/'pid').write_text(str(p.pid));(VM/'launch.json').write_text(json.dumps({'args':args,'pid':p.pid,'started':time.time()},indent=2)+'\n')
    print('Started cardless application VM, PID',p.pid)
def screen():
    monitor('screendump '+str(VM/'screen.ppm'))
    from PIL import Image
    Image.open(VM/'screen.ppm').save(VM/'screen.png');print(VM/'screen.png')
def click(text, mode="click"):
    x,y=map(int,text.split(','))
    width,height=map(int,(VM/'screen.ppm').read_bytes().split(b'\n',3)[1].split())
    if not (0<=x<width and 0<=y<height):raise ValueError('Click outside screenshot')
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(5);sock.connect(str(SOCKET)+'.qmp');stream=sock.makefile('rwb');stream.readline()
        def request(execute,args=None):
            obj={'execute':execute}
            if args is not None:obj['arguments']=args
            stream.write(json.dumps(obj).encode()+b'\n');stream.flush()
            while True:
                out=json.loads(stream.readline())
                if 'return' in out:return out
                if 'error' in out:raise RuntimeError(out)
        request('qmp_capabilities')
        request('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':x*32767//(width-1)}},{'type':'abs','data':{'axis':'y','value':y*32767//(height-1)}}]})
        time.sleep(.3)
        if mode=='move':return
        for _ in range(2 if mode=='doubleclick' else 1):
            request('input-send-event',{'events':[{'type':'btn','data':{'button':'left','down':True}}]});time.sleep(.05 if mode=='doubleclick' else .2)
            request('input-send-event',{'events':[{'type':'btn','data':{'button':'left','down':False}}]});time.sleep(.1 if mode=='doubleclick' else .8)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['start','status','screen','type','key','command','stop','click','move','doubleclick','write']);ap.add_argument('text',nargs='?',default='');ap.add_argument('--installed',action='store_true');ap.add_argument('--memory-mib',type=int,choices=[4096,8192],default=None);ap.add_argument('--kvm',action='store_true',help='explicit KVM with -cpu host; fails if unavailable');a=ap.parse_args()
    if a.action=='start':start(a.installed,a.memory_mib or (8192 if a.kvm else 4096),a.kvm)
    elif a.action=='status':
        try: result=monitor('info status')
        except (FileNotFoundError,ConnectionRefusedError):print('VM status: stopped')
        else:
            for line in result.splitlines():
                if line.startswith('VM status:'):print(line)
            print((VM/'qemu.out').read_text()[-2000:])
    elif a.action=='screen':screen()
    elif a.action=='type':type_line(a.text)
    elif a.action=='write':type_line(a.text,False)
    elif a.action=='key':
        monitor('sendkey '+a.text);time.sleep(.15)
    elif a.action=='command':
        allowed={'info status','info mice','info pci','info qtree','info version','info block','info name','info cpus'}
        if a.text not in allowed:raise SystemExit('Only read-only monitor inventory commands are allowed')
        print(monitor(a.text))
    elif a.action in ('click','move','doubleclick'):click(a.text,a.action)
    elif a.action=='stop':print(monitor('quit'))
if __name__=='__main__':main()
