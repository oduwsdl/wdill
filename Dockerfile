FROM	node:latest

# Install service requirements
RUN 	apt-get update \
		&& apt-get install -y \
		python3 \
		python3-pip \
		cron \
		ffmpeg \
		imagemagick

ADD	. /wdill

RUN 	chmod +x /wdill/*

# Add crontab file in the cron directory
ADD 	crontab /etc/cron.d/wdill-cron

# Give execution rights on the cron job
RUN 	chmod 0644 /etc/cron.d/wdill-cron

# Create the log file to be able to run tail
RUN 	touch /var/log/cron.log

WORKDIR /wdill

# Install Python dependencies
RUN 	pip3 install -r requirements.txt

# Install NodeJS dependencies
RUN 	npm install

# Run the command on container startup
CMD 	cron && tail -f /var/log/cron.log
