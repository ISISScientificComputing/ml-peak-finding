Running Persistent Container
============================

We need to use and share a single container between different users. We also
need to make available, inside the container, some files from outside of the
container.

To do this, a container should be launched, with a specific name known to all,
with a volume mounted at a known shared location. This only needs to be done
once per persistent environment we want to share, after which it can be used
as described in the following sections.

As an example, I have launched a container like this:
```
$ sudo docker run -itd --name peakstest -v /path/on/host/peaks-share:/peaks-share mlpeaks
```
This breaks down as follows:
- `-itd`: an `i`nteractive `t`erminal is launched in `d`etached mode
- The container is given the name `peakstest`
- `/path/on/host/peaks-share` is mounted to `/peaks-share` inside container
- The image being launched is called `mlpeaks`


List Available Containers
-------------------------

You can check the names or statuses of available containers:
```
$ sudo docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
c71604cc0d3f        mlpeaks             "/bin/bash"         17 minutes ago      Up 17 minutes                           peakstest
```


Exec into Running Container
---------------------------

Generally, to use a shared container, you will want to execute a new shell
inside of it, like this:
```
$ sudo docker exec -it peakstest bash
root@c71604cc0d3f:/# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  18172  1880 ?        Ss+  10:55   0:00 /bin/bash
root        62  1.0  0.0  18180  1944 ?        Ss   11:17   0:00 bash
root        77  0.0  0.0  15572  1112 ?        R+   11:17   0:00 ps aux
root@c71604cc0d3f:/# exit
exit
$ 
```
Note you must provide the name (or ID) of the container, not an image.

You can also execute some other process directly:
```
$ sudo docker exec -it peakstest mantidpython
```

Exiting only shuts down the current process, the container continues to run.


Attaching to the Primary Shell
------------------------------

You may have noticed a `/bin/bash` process with PID 1 above. This is the main
container process. Usually this is not needed, but you can attach to it like
this:

```
$ sudo docker attach peakstest
root@c71604cc0d3f:/# 
```
If you exit now, this will shut down the container and all of its processes.

If you want to detach again without shutting down, hold `CTRL` and press `p`,
then `q`.


Restarting a Stopped Container
------------------------------

A running container can be stopped by exiting the primary process, as shown
above, or by running:
```
$ sudo docker stop peakstest
$ sudo docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS                      PORTS               NAMES
c71604cc0d3f        mlpeaks             "/bin/bash"         3 hours ago         Exited (0) 12 seconds ago                       peakstest
```
It might also be stopped by the machine restarting or crashing.

You could start a new instance by following the instructions of the first
section of this document, but then everything done inside the container would
be reset (except what was saved to the mounted volume).

If you want to restart the same container, and restore the previous state, you
can do this by running the following command:
```
$ sudo docker start peakstest
$ sudo docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
c71604cc0d3f        mlpeaks             "/bin/bash"         3 hours ago         Up 20 seconds                           peakstest
```
