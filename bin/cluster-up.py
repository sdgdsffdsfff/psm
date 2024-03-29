import os
import sys
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# check dependency
if not os.path.exists('%s/comp/jdk/bin/java' % BASE_DIR):
    print('missing java: http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html')
    sys.exit()

if not os.path.exists('%s/comp/zookeeper/bin/zkServer.sh' % BASE_DIR):
    print('missing zookeeper: http://apache.mirrors.pair.com/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz')
    sys.exit()

if not os.path.exists('%s/comp/consul' % BASE_DIR):
    print('missing consul: https://dl.bintray.com/mitchellh/consul/0.5.2_linux_amd64.zip')
    sys.exit()

if not os.path.exists('%s/comp/consul-webui' % BASE_DIR):
    print('missing consul webui: https://dl.bintray.com/mitchellh/consul/0.5.2_web_ui.zip')
    sys.exit()

if not os.path.exists('%s/comp/marathon/bin/start' % BASE_DIR):
    print('missing marathon: http://downloads.mesosphere.com/marathon/v0.8.2/marathon-0.8.2.tgz')
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
for mesos_no in [1, 2, 3]:
    if '172.17.100.%s' % (3 + mesos_no) not in ifconfig_output:
        subprocess.check_call('sudo ifconfig lo:mesos%s 172.17.100.%s' % (mesos_no, 3 + mesos_no), shell=True)
for slave_no in [1, 2, 3, 4, 5]:
    if '172.17.100.%s' % (6 + slave_no) not in ifconfig_output:
        subprocess.check_call('sudo ifconfig lo:slave%s 172.17.100.%s' % (slave_no, 6 + slave_no), shell=True)
for marathon_no in [1, 2, 3]:
    if '172.17.100.%s' % (11 + marathon_no) not in ifconfig_output:
        subprocess.check_call('sudo ifconfig lo:marathon%s 172.17.100.%s' % (marathon_no, 11 + marathon_no), shell=True)
for consul_no in [1, 2, 3]:
    if '172.17.100.%s' % (14 + consul_no) not in ifconfig_output:
        subprocess.check_call('sudo ifconfig lo:consul%s 172.17.100.%s' % (consul_no, 14 + consul_no), shell=True)

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
    subprocess.check_call(
        'cp %s/comp/zookeeper/conf/log4j.properties %s/var/cfg/zk%s/log4j.properties' % (BASE_DIR, BASE_DIR, zk_no),
        shell=True)

# mesos
for mesos_no in [1, 2, 3]:
    if not os.path.exists('%s/var/data/mesos-master%s' % (BASE_DIR, mesos_no)):
        os.makedirs('%s/var/data/mesos-master%s' % (BASE_DIR, mesos_no))
linux_dist = platform.dist()[0]
if 'Ubuntu' == linux_dist:
    if 'E56151BF' not in subprocess.check_output('apt-key list', shell=True):
        subprocess.check_call(
            'sudo apt-key adv --keyserver-options http-proxy=http://10.223.41.11:8444 --keyserver keyserver.ubuntu.com --recv E56151BF',
            shell=True, env=os.environ)
    DISTRO = 'ubuntu'
    CODENAME = 'trusty'
    subprocess.check_output(
        'echo "deb http://repos.mesosphere.io/%s %s main" | sudo tee /etc/apt/sources.list.d/mesosphere.list' % (
        DISTRO, CODENAME), shell=True)
    installed_packages = subprocess.check_output('dpkg --get-selections', shell=True)
    missing_packages = []
    for dep in ['mesos']:
        if dep not in installed_packages:
            missing_packages.append(dep)
    if missing_packages:
        print('install missing packages: %s' % missing_packages)
        print('=================')
        os.system('sudo apt-get update')
        os.system('sudo apt-get install %s' % ' '.join(missing_packages))
    if not os.path.exists('/etc/init/zookeeper.override'):
        subprocess.check_call('echo manual | sudo tee /etc/init/zookeeper.override', shell=True)
        subprocess.check_call('sudo service zookeeper stop', shell=True)
    if not os.path.exists('/etc/init/mesos-master.override'):
        subprocess.check_call('echo manual | sudo tee /etc/init/mesos-master.override', shell=True)
        try:
            subprocess.check_call('sudo service mesos-master stop', shell=True)
        except:
            pass
    if not os.path.exists('/etc/init/mesos-slave.override'):
        subprocess.check_call('echo manual | sudo tee /etc/init/mesos-slave.override', shell=True)
        try:
            subprocess.check_call('sudo service mesos-slave stop', shell=True)
        except:
            pass
else:
    raise Exception('not supported platform: %s' % linux_dist)

# consul
for consul_no in [1, 2, 3]:
    if not os.path.exists('%s/var/data/consul-server%s' % (BASE_DIR, consul_no)):
        os.makedirs('%s/var/data/consul-server%s' % (BASE_DIR, consul_no))
for slave_no in [1, 2, 3, 4, 5]:
    if not os.path.exists('%s/var/data/consul-agent%s' % (BASE_DIR, slave_no)):
        os.makedirs('%s/var/data/consul-agent%s' % (BASE_DIR, slave_no))

# start the cluster
os.environ['JAVA_HOME'] = '%s/comp/jdk' % BASE_DIR
subprocess.check_call('supervisord -c %s/var/cfg/supervisor.cfg' % BASE_DIR, shell=True)
