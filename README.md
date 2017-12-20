# On Your Mark, Get Set, Scrape !!

This repository holds the code for scrapers built under the project "Scrape the Planet"  
- Methods used for scraping : Scrapy   
- Language used for scraping : Python3.X.X

**Minutes of the meeting:** http://bit.ly/scrapeThePlanet

## Installation
Clone the repository (or download it). Then, follow the installation steps to run the spiders.

### Create a Virtual Environemnt
```
python3 -m venv VENV_NAME
```
or
```
virtualenv -p python3 VENV_NAME
```

### Activate the venv
Windows: `VENV_NAME/Scripts/activate`

Linux: `source VENV_NAME/bin/activate`

### Install the requirements
Navigate to repository: `pip install -r requirements.txt`

- Requirements(For scraping):
    - Python3
    - TOR
    - Privoxy

- Requirements(For database):
    - psycopg2

- Requirements(For flask Application):
    - flask

- Requirements(for Deploying)
   - Scrapyd
   - Scrapyd-Client ( Use ```pip install git+https://github.com/scrapy/scrapyd-client``` )


### Install TOR and Privoxy

#### Install TOR
```
sudo apt-get install tor
```
#### Install Privoxy
```
sudo apt-get install privoxy
```
#### Configure Privoxy to route TOR
Add following lines at the end of  ```/etc/privoxy/config```
```
forward-socks5  / 127.0.0.1:9050 .
forward-socks4a / 127.0.0.1:9050 .
forward-socks5t / 127.0.0.1:9050 .
```

### Database Setup (PostgreSQL)

- Installation in Debian: `sudo apt-get install postgresql postgresql-contrib`

- Configurations:
	- config: `/etc/postgresql/9.5/main`  
	- data:   `/var/lib/postgresql/9.5/main`
	- socket: `/var/run/postgresql`
	- port:   `5432`

- Make User:
	**Note: Your USERNAME and PASSWORD must contain only smallcase characters.**
	- `sudo -i -u postgres`
	- `createuser YOUR_ROLE_NAME/YOUR_USERNAME --interactive --pwprompt`

- Setup Database:
    - Create file a ```add_env.sh```; Inside it, Write:
    ```bash
    #!/bin/bash

    export SCRAPER_DB_HOST=localhost
    export SCRAPER_DB_USER=YOUR_ROLE_NAME/YOUR_USERNAME
    export SCRAPER_DB_PASS=YOUR_PASSWORD
    export SCRAPER_DB_NAME=YOUR_DATABASE_NAME
    export FLASK_APP=server.py
    ```

### Configuring your spiders

Add the following inside your spider class,

```python

custom_settings = {
    'site_name': "asianage",
    'site_url': "http://www.asianage.com/newsmakers",
}
```

### Run Spiders
**Note: Navigate to the folder containing scrapy.cfg**
In order to run spiders, make sure:
- PostgreSQL Server is running
- TOR and Privoxy are running
```
scrapy crawl SPIDER_NAME
```
- SPIDER_NAME List:
    1. indianExpressTech
    2. indiaTv  
    3. timeTech
    4. ndtv
    5. inshorts
    6. zeeNews
    7. News18Spider
    8. moneyControl
    9. oneindia
    10. oneindiaHindi
    11. firstpostHindi
    12. firstpostSports
    13. newsx
    14. hindustantimes
    15. asianage
    16. timeNews
    17. newsNation [In development]

### Objects Available for Spiders
- site_id: Contains SITE_ID for a spider, fetched from database
- url_stats: Contains the dictionary ```{'parsed': 0, 'stored': 0, 'scraped': 0, 'dropped': 0}```
- dbconn: DatabaseManager() Object dedicated for the spider
- log_id: Contains the id of Database Log Being Used

All the above objects can be used inside a spider using ```self.object_name``` and in pipelines using spider object ```spider.object_name```

### Additional Utilities 

- scrapeNews.db.DatabaseManager
    - Consists of Various Database Related Utilities
    - ```urlExists(url)```: Returns Bool. Checks if the given link is present in database

- scrapeNews.db.LogsManager
    - Consists Methods for Managing Spider Run Stats

- scrapeNews.settings.logger
    - Preconfigured Logger, import it and use like ```logger.error(__name__ + " Your_ERROR")```

## Deploying (Server Instructions)

### Create a new Tmux Session
```
tmux
```
### Install & Activate a Virtual Environment on Server
```
virtualenv -p python3 venv
source venv/bin/activate
```

#### Install Requirements
```
pip install -r requirements.txt
```
**Note:** This step is crucial, incase of missing dependencies no spiders will be deployed.

#### Add Environment Variables
```
source add_anv.sh
``` 

#### Install Scrapyd (if not already)
```
pip install scrapyd
```
#### Start the scrapyd server
```
scrapyd
```

#### Create a new window and start scheduler script
```
ctrl+b c
```
```
vitualenv -p python3 venv-scheduler
source venv-scheduler/bin/activate
pip install schedule requests
python scheduler.py
```

## Deploying (Client Instructions)

Once the Scrapyd Server is up and running, on the same machine do the following:
Instructions Below Assume you have a virtualenv setup with requirements installed and environment variables added.

### Install Scrapyd-Client
```
pip install git+https://github.com/scrapy/scrapyd-client
```

### Deploy
```
scrapyd-deploy
```

All Set!

Instructions for Web App, COMING SOON!
