import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# check dependency
if not os.path.exists('%s/comp/jdk/bin/java' % BASE_DIR):
    print('missing java: http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html')
    sys.exit()

if not os.path.exists('%s/comp/zookeeper/bin/zkServer.sh' % BASE_DIR):
    print('missing zookeeper: http://apache.mirrors.pair.com/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz')
    sys.exit()

try:
    SUPERVISORD = subprocess.check_output('which supervisord', shell=True).strip()
    SUPERVISORCTL = subprocess.check_output('which supervisorctl', shell=True).strip()
except:
    print('missing supervisord: apt-get supervisor')
    sys.exit()

# create common dirs
for sub_dir in ['cfg', 'run', 'log', 'data']:
    if not os.path.exists('%s/var/%s' % (BASE_DIR, sub_dir)):
        os.makedirs('%s/var/%s' % (BASE_DIR, sub_dir))

# create network
ifconfig_output = subprocess.check_output('ifconfig')
for zk_no in [1, 2, 3]:
    if '172.17.100.%s' % zk_no not in ifconfig_output:
        subprocess.check_call('sudo ifconfig lo:zk%s 172.17.100.%s' % (zk_no, zk_no), shell=True)

# supervisor
if not os.path.exists('%s/var/log/supervisor' % BASE_DIR):
    os.makedirs('%s/var/log/supervisor' % BASE_DIR)
with open('%s/etc/supervisor.cfg' % BASE_DIR) as f:
    supervisor_cfg = f.read().replace('${BASE_DIR}', BASE_DIR)
with open('%s/var/cfg/supervisor.cfg' % BASE_DIR, 'w') as f:
    f.write(supervisor_cfg)

# zookeeper
for zk_no in [1, 2, 3]:
    if not os.path.exists('%s/var/cfg/zk%s' % (BASE_DIR, zk_no)):
        os.makedirs('%s/var/cfg/zk%s' % (BASE_DIR, zk_no))
    if not os.path.exists('%s/var/log/zk%s' % (BASE_DIR, zk_no)):
        os.makedirs('%s/var/log/zk%s' % (BASE_DIR, zk_no))
    if not os.path.exists('%s/var/data/zk%s' % (BASE_DIR, zk_no)):
        os.makedirs('%s/var/data/zk%s' % (BASE_DIR, zk_no))
    with open('%s/var/data/zk%s/myid' % (BASE_DIR, zk_no), 'w') as f:
        f.write(str(zk_no))
    with open('%s/etc/zk.cfg' % BASE_DIR) as f:
        zk_cfg = f.read().replace('${BASE_DIR}', BASE_DIR)
        zk_cfg = zk_cfg.replace('${clientPortAddress}', '172.17.100.%s' % zk_no)
        zk_cfg = zk_cfg.replace('${dataDir}', '%s/var/data/zk%s' % (BASE_DIR, zk_no))
    with open('%s/var/cfg/zk%s/zk.cfg' % (BASE_DIR, zk_no), 'w') as f:
        f.write(zk_cfg)
    with open('%s/etc/zookeeper-env.sh' % BASE_DIR) as f:
        zookeeper_env_sh = f.read().replace('${BASE_DIR}', BASE_DIR)
        zookeeper_env_sh = zookeeper_env_sh.replace('${zk_no}', str(zk_no))
    with open('%s/var/cfg/zk%s/zookeeper-env.sh' % (BASE_DIR, zk_no), 'w') as f:
        f.write(zookeeper_env_sh)

os.environ['JAVA_HOME'] = '%s/comp/jdk' % BASE_DIR
subprocess.check_call('supervisord -c %s/var/cfg/supervisor.cfg' % BASE_DIR, shell=True)