FROM	nikolaik/python-nodejs:latest

# Install service requirements
RUN 	apt-get update \
		&& apt-get install -y wget gnupg ca-certificates cron ffmpeg imagemagick ghostscript\
		&& wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
		&& sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
		&& apt-get update \
		&& apt-get install -y google-chrome-stable \
		&& rm -rf /var/lib/apt/lists/*


ADD	. /wdill

RUN 	chmod +x /wdill/*

WORKDIR /wdill

# Replace path placeholders with project location
RUN 	sed -i "s@<WDILL_PATH>@/wdill@" crontab
RUN		sed -i "s@<WDILL_PATH>@/wdill@" execute_wdill.sh

# Add crontab file in the cron directory
ADD 	crontab /etc/cron.d/wdill-cron

RUN		sed -i "s@<WDILL_PATH>@/wdill@" /etc/cron.d/wdill-cron

# Give execution rights on the cron job
RUN 	chmod 0644 /etc/cron.d/wdill-cron

# Create the log file to be able to run tail
RUN 	touch /var/log/cron.log

# Install Python dependencies
RUN 	pip3 install -r requirements.txt

# Install NodeJS dependencies
RUN 	npm install

# Run the command on container startup
CMD 	cron && tail -f /var/log/cron.log
