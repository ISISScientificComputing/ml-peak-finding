Installing Docker on Autoreduction Machine
------------------------------------------

This sections details the steps taken to install docker on the autoreduction
machine.

Docker is not currently available on default repositories on RHEL.

Most documentation available, for installing Docker on RHEL, described how to
install `docker-ee`. However, this is the Enterprise Edition and requires
purchasing a special license.

Instead, the following steps can be used to instal the community edition, 
`docker-ce`, from the CentOS repositories.

```
$ sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
$ sudo yum makecache fast
$ sudo yum install docker-ce
$ sudo systemctl start docker
$ sudo docker run hello-world
```
The last step is just for verifying.


Changing Location of Docker Image Repo
--------------------------------------

By default, Docker stores its image repository, along with all built and
downloaded images and all container filesystems, in `/var/lib/docker`.

This is an issue on the autoreduction machine, since `/var` has very limited
space on it. Building a large image can easily exhaust the entire remaining
space on that mount point. As a result, the docker root directory had to be
moved somewhere else.

At least for the time being, I decided to move it into my home directory.
This does not prevent other users from running or creating Docker images,
since the Docker service runs as root.

The following steps were used to change the Docker root directory on RHEL:
```
$ sudo nano /lib/systemd/system/docker.service
[[[
- Edit to change (line 11) from ...
ExecStart=/usr/bin/dockerd
- ... to ...
ExecStart=/usr/bin/dockerd -g /home/[username]/docker
]]]
$ sudo systemctl daemon-reload
$ sudo systemctl restart docker
$ sudo docker info | grep -i 'root dir'
```
The last step is just for verifying.

