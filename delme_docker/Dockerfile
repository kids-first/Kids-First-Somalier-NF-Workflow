FROM ubuntu:24.04

RUN apt update && apt install -y wget
RUN wget https://github.com/brentp/somalier/releases/download/v0.3.1/somalier \
&& chmod +x somalier \
&& mv somalier /usr/local/bin/