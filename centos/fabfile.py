#!/usr/bin/env python
# encoding: utf-8
'''
fabfile -- automation deployment tools.

@author:     FengXi

USAGE:
    fab -H xf5,xf6,xf8 --user=root --password='your_password' --parallel --pool-size=8 setup_env

'''
import os
from StringIO import StringIO
import tempfile

from fabric.api import sudo, local, run, get, put, env, cd, settings
from fabric.contrib.files import append, exists

def setup_env():
    """
    setup centos environments
    """
    #with settings(warn_only=True):
    ssh_no_pwd()
    create_ssh_key()
    install_gfw_hosts()
    update_os()
    install_epel_repo()
    install_basic_tools()
    install_dotfiles()
    motd()

def ssh_no_pwd(local_key_file='~/.ssh/id_rsa.pub', remote_key_dir='~root'):
    """
    push ssh public key to remote server(s).
    """
    remote_authorized_keys = "%s/.ssh/authorized_keys" % remote_key_dir

    with settings(warn_only=True):
        run("mkdir -p %s/.ssh" % remote_key_dir)
    if exists(remote_authorized_keys) is None:
        run("touch %s " % remote_authorized_keys)


    def _read_local_key_file(local_key_file):
        local_key_file = os.path.expanduser(local_key_file)
        with open(local_key_file) as f:
            return f.read()

    key = _read_local_key_file(local_key_file)

    with settings(warn_only=True):
        # check if the public exists on remote server.
        ret = run("grep -q '%s' '%s'" %  (key, remote_authorized_keys))
        if ret.return_code == 0:
            pass
        else:
            append(remote_authorized_keys, key)
            run("chmod 600 %s" % remote_authorized_keys)

def create_ssh_key():
    """
    create local ssh keys
    """
    local_key_dir = '/root/.ssh/id_rsa'
    run("echo -e 'y\n' | ssh-keygen -t rsa -N '' -f %s" % local_key_dir)

def download_ssh_keys():
    """
    ssh wo passwod between remote servers.
    """
    # read remote keys to local
    local_temp_file = "/tmp/.id_rsa.pub.%s" % env.host
    with settings(warn_only=True):
        local("rm -rf %s" % local_temp_file)
        get(local_path=local_temp_file, remote_path="/root/.ssh/id_rsa.pub")

def copy_ssh_keys():
    """
    copy all ssh keys to remote
    """
    for host in env.hosts:
        if host != env.host:
            with settings(warn_only=True):
                local_temp_file = "/tmp/.id_rsa.pub.%s" % host
                ssh_no_pwd(local_key_file=local_temp_file, remote_key_dir='~root')

def update_os():
    """
    yum update -y os
    """
    sudo("yum update -y")

def install_basic_tools():
    """
    install some basic tools
    """
    sudo("yum install -y vim git rsync unzip wget net-tools telnet bind-utils bash-completion fabric ")

def install_epel_repo():
    """
    install yum epel release repo
    """
    sudo("yum install -y epel-release")

def install_dotfiles():
    """
    install my dotfiles from github
    """
    tmp_dir = "/tmp/"

    with settings(warn_only=True):
        with cd(tmp_dir):
            run("git clone https://github.com/westwin/dotfiles.git dotfiles")
            run("bash %s/dotfiles/install.sh" % tmp_dir)

        run("rm -rf %s/dotfiles" % tmp_dir)

def install_gfw_hosts():
    """
    install GFW hosts file
    """
    put(local_path="./hosts", remote_path="/etc/hosts", mirror_local_mode=True)


def motd():
    """
    motd text
    """
    run("echo %s >/etc/motd" % "I LOVE YOU, AGNES !")


def stop_firewall():
    """
    shutdown firewall
    """
    with settings(warn_only=True):
        sudo("systemctl stop firewalld")
        sudo("systemctl disable firewalld")
