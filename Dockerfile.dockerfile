FROM ubuntu:22.04

RUN groupadd -r valheim && useradd -r -g valheim valheim

WORKDIR /home/valheim

RUN apt update && \
    apt install -y software-properties-common && \
    add-apt-repository multiverse && \
    dpkg --add-architecture i386

RUN apt update && \
    echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    apt install -y \
        python3 \
        python3-pip \
        libpulse-dev \
        libatomic1 \
        libc6-i386 \
        libc6
RUN pip3 install requests
RUN apt install -y steamcmd

RUN mkdir /home/valheim/valheim-server
COPY valheim-telegram-bot-and-server.py /home/valheim/valheim-server/
RUN chown -R valheim:valheim /home/valheim

USER valheim

CMD ["python3", "/home/valheim/valheim-server/valheim-telegram-bot-and-server.py"]
