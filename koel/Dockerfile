FROM binhex/arch-koel
MAINTAINER kellertobi

# additional files
##################

RUN pacman -S --needed python3 mysql-python --noconfirm
# add pre-configured config files for nobody
ADD m3usync/* /root/

# map /config to host defined config path (used to store configuration from app)
VOLUME /config

# expose port for https
EXPOSE 8060

# set environment variables for user nobody
ENV HOME /home/nobody

# set permissions
#################
RUN echo $(cat /root/m3usync-supervisor.conf) >> /etc/supervisor/conf.d/koel.conf

# run script to set uid, gid and permissions
CMD ["/bin/bash", "/root/init.sh"]