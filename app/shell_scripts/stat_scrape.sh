#!bin/bash
export PATH=$PATH:/usr/local/bin
export POSTGRES_USER=$POSTGRES_USER 
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD 
export POSTGRES_DB=$POSTGRES_DB
export POSTGRES_HOST=$POSTGRES_HOST 
export POSTGRES_PORT=$POSTGRES_PORT 
cd "/stat_scrape";
scrapy crawl ufcstatspider
# stat_scrape.sh is the script that is used to scrape the data from the UFC stats website.