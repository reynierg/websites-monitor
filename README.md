Websites monitor

- [DESCRIPTION](#description)
- [SOLUTION](#solution)
- [DEV-DEPENDENCIES](#dev-dependencies)  
- [CONFIGURATION](#configuration)
- [RUN](#run)
- [RUN-TESTS](#run-tests)
- [TODO](#todo)
- [REFERENCES](#references)

# DESCRIPTION

Websites monitor is a system for the periodic monitoring of certain statistics related 
to the status of preconfigured websites. The following parameters are persisted, 
regarding the status check of a website:
- **url**: Url of the website checked
- **error_code**: Error code as a result of visiting the site. It includes 200 OK. If 
  there was some error, which is not directly related to HTTP, other error codes will 
  be used, like 404(for failed DNS name resolution) or 599(for TCP connection time 
  out). When the error while trying to visit the url, isn't any of the previously 
  mentioned, the default value of -1 will be used.
- **response_time**: Response's time while making a GET request to the url.
- **regex_pattern**: Pattern to be applied to the response's HTML payload, when the 
  GET request succeeds.
- **matched_text**: Matched text in the response's HTML payload, with the specified 
  regex_pattern.
  
# SOLUTION

The solution was implemented using an event-driven architecture using microservices.<br>
It consists of two microservices: a Monitor and a Consumer.<br>
The execution of the microservices is managed using [Docker Compose](https://docs.docker.com/compose/).

## Monitor

It's a service implemented as a web crawler, using [Scrapy](https://scrapy.org/), which is a fast 
high-level framework based on the [Twisted](https://twistedmatrix.com/trac/) event-driven network programing framework. 
Periodically, it queries the websites specified in the corresponding configuration 
file, and stores the metrics corresponding to each website in an instance of [Apache Kafka](https://kafka.apache.org/).

## Consumer

This service polls website metrics from the Apache Kafka server and stores them in a 
[PostgreSQL](https://www.postgresql.org/) database.<br>
Regarding the implementation details:<br>
- A dedicated thread is created to polling the websites' metrics from the Kafka server. 
  The obtained metrics are fed to the main thread through a thread-safe queue.
- The main execution thread, feeds the metrics to a bounded Thread Pool Executor to be 
  stored in the PostgreSQL database.
- The Thread Pool Executor's threads use a bounded database connection pool to access 
  the database server.
- The service implements graceful shutdown, and by default, persist in the database 
  any acquired metrics from Kafka, before shut-down.  
  
## Database

The schema of the PostgreSQL database being used by the `Consumer` to store the metrics is depicted in the following image.<br>
It consists of two tables `websites` and `metrics`, with a 1:M relationship between them:<br>
![alt text](https://github.com/reynierg/websites-monitor/blob/main/images/db_schema.png "Database schema")


# DEV-DEPENDENCIES

For development purpose, source code quality analysis, detection of errors and for running tests, 
the following dependencies are required:

- [tox](https://tox.readthedocs.io/en/latest/)
- [flake8](https://flake8.pycqa.org/en/latest/)
- [pylint](https://www.pylint.org/)
- [mypy](https://mypy.readthedocs.io/en/stable/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)

# CONFIGURATION

- Clone the project executing the following command in a terminal:\
`git clone https://github.com/reynierg/websites-monitor.git`
- Make sure to copy the Kafka required certificates and key files to the folder 
  `kafka_certs`. The expected file names are `ca.pem`, `service.cert` and `service.key`
- **monitor**: In the `docker-compose.yml` file that is in the project' root directory, 
  update the following environment variables properly: `TOPIC_NAME`, 
  `BOOTSTRAP_SERVERS`. <br>
  By default, the websites urls are parsed from an existing CSV file located on 
  `monitor/data/urls.csv`. Modify the content of the file to your needs<br>
  To parse the urls from a JSON file instead, update the file in 
  `monitor/data/urls.json` and uncomment the following line in the 
  `docker-compose.yaml` file:<br>
  `URLS_PROVIDER_TYPE=JsonUrlsProvider`
- **consumer**: In the `docker-compose.yml` file that is in the project's root 
  directory, update the following environment variables properly: `TOPIC_NAME`, 
  `PG_URI`, `BOOTSTRAP_SERVERS`.<br>
  By default, when the service is asked to abort execution, it will wait for that all 
  the already acquired websites' metrics from Kafka, to be persisted in the database, 
  before shut-down. To change this behaviour, uncomment the following line in the 
  `docker-compose.yaml` file:<br>
  `DROP_MESSAGES_IF_ABORT=1`<br>
  Keep in mind that in that case, most probably they will be lost forever, because of 
  auto-commit offset.

# RUN

Open two terminals(one for run every service), and in both of them, navigate to the 
project directory using:\
`cd websites-monitor`

For execute the websites monitor, execute the following command:<br>
`sudo make run-monitor`
This command will build the corresponding docker image the first time, and will run 
it.<br>

For execute the consumer, execute the following command:<br>
`sudo make run-consumer`
This command will build the corresponding docker image the first time, and will run 
it.<br>

# RUN-TESTS

For run the linters and tests, first will be needed to install the development 
requirements:
## Create and activate a virtual environment
Being in the project directory, execute the following commands:
```
python3 -m venv venv
. venv/bin/activate
```

## Install the development dependencies
`pip install -r requirements-dev.txt`

## Run the tests
Once installed the dependencies, is only necessary to execute "tox", and it will take 
care of run "flake8", "pylint", "mypy" and the tests using "pytest":\
`tox`

If the tests run successfully, in a directory named "htmlcov", will be created html 
files with the test coverage report and in the terminal will appear the names of the 
executed tests, and a summary of the test's coverage.

# TODO
- Use [Apache Avro](https://www.confluent.io/blog/avro-kafka-data/) as a serialization 
  protocol for the Kafka messages. Avro is a data serialization system. Combined with 
  Kafka, it provides schema-based, robust, and fast binary serialization. 
- Create installation packages.
- Write more unit tests for both services.
- Write integration tests for the `monitor` and `consumer`.
- Improve the test's coverage to get it to around a 90%.
- Configure CI/CD.
- Deploy the `monitor` crawler to some distributed crawler management infrastructure 
  like [Scrapyd](https://scrapyd.readthedocs.io/en/stable/) or 
  [Gerapy](https://docs.gerapy.com/en/latest/).

# REFERENCES

[Getting started with Aiven for Apache Kafka](https://help.aiven.io/en/articles/489572-getting-started-with-aiven-for-apache-kafka)

[Data streaming made easy with Apache Kafka](https://aiven.io/blog/data-streaming-made-simple-with-apache-kafka)

[Create your own data stream for Kafka with Python and Faker](https://aiven.io/blog/create-your-own-data-stream-for-kafka-with-python-and-faker)

[Viewing and Resetting Consumer Group Offsets](https://help.aiven.io/en/articles/2661525-viewing-and-resetting-consumer-group-offsets)

[Aiven PostgreSQL tutorial](https://aiven.io/blog/aiven-postgresql-tutorial)

[An introduction to PostgreSQL(Aiven)](https://aiven.io/blog/an-introduction-to-postgresql)

[Python Postgres psycopg2 ThreadedConnectionPool exhausted](https://stackoverflow.com/questions/48532301/python-postgres-psycopg2-threadedconnectionpool-exhausted)

[kafka-python API](https://kafka-python.readthedocs.io/en/master/apidoc/modules.html)

[TheadPoolExecutor with a bounded queue in Python](https://www.bettercodebytes.com/theadpoolexecutor-with-a-bounded-queue-in-python/)

[Holy grail of graceful shutdown in Python](https://github.com/wbenny/python-graceful-shutdown)

[Scrapy 2.4 documentation](https://docs.scrapy.org/en/latest/)

[Welcome to Mypy documentation!](https://mypy.readthedocs.io/en/stable/)

[Welcome to the tox automation project](https://tox.readthedocs.io/en/latest/)

[unittest.mock — mock object library](https://docs.python.org/3/library/unittest.mock.html)

[pytest: helps you write better programs](https://docs.pytest.org/en/stable/)
