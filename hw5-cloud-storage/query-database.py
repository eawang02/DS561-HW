
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import os
from dotenv import load_dotenv

load_dotenv()
config = os.environ
connector = Connector()

# function to return the database connection object
def getconn():
    conn = connector.connect(
        config['INSTANCE_CONNECTION_NAME'],
        "pymysql",
        user=config['DATABASE_USER'],
        password=config['DATABASE_PASSWORD'],
        db=config['DATABASE_NAME'],
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# insert data into our ratings table
insert_req = sqlalchemy.text(
    "INSERT INTO all_requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file) "
    "VALUES (:country, :client_ip, :gender, :age, :income, :is_banned, :time_of_day, :requested_file);",
)

insert_invalid = sqlalchemy.text(
    "INSERT INTO invalid_requests (id, time_of_day, requested_file, error_code) "
    "VALUES (:id, :time_of_day, :requested_file, :error_code);",
)


def fetchAllDatabase():
    # connect to connection pool
    with pool.connect() as db_conn:
        # query and fetch ratings table
        valid_results = db_conn.execute(sqlalchemy.text("SELECT * FROM all_requests")).fetchall()
        invalid_results = db_conn.execute(sqlalchemy.text("SELECT * FROM invalid_requests")).fetchall()


        # show results

        print("all_requests table:")
        for row in valid_results:
            print(row)

        print("invalid_requests table:")
        for row in invalid_results:
            print(row)

def describeDatabase():
    with pool.connect() as db_conn:
        describeReq = db_conn.execute(sqlalchemy.text("DESCRIBE all_requests")).fetchall()
        print(describeReq)
        describeInv = db_conn.execute(sqlalchemy.text("DESCRIBE invalid_requests")).fetchall()
        print(describeInv)


def resetDatabase():
    print("Resetting database...")

    # connect to connection pool
    with pool.connect() as db_conn:
        # Reset tables
        db_conn.execute(
            sqlalchemy.text(
                "DROP TABLE IF EXISTS invalid_requests;"
            )
        )

        db_conn.execute(
            sqlalchemy.text(
                "DROP TABLE IF EXISTS all_requests;"
            )
        )

        db_conn.execute(
            sqlalchemy.text(
                "CREATE TABLE IF NOT EXISTS all_requests "
                "( id SERIAL NOT NULL AUTO_INCREMENT, country VARCHAR(255) NOT NULL, "
                "client_ip VARCHAR(15) NOT NULL, gender VARCHAR(255) NOT NULL, "
                "age VARCHAR(255) NOT NULL, income VARCHAR(255) NOT NULL, "
                "is_banned BOOL NOT NULL, time_of_day DATETIME NOT NULL, "
                "requested_file VARCHAR(255), "
                "PRIMARY KEY (id));"
                )
        )

        db_conn.execute(
            sqlalchemy.text(
                "CREATE TABLE IF NOT EXISTS invalid_requests "
                "( id SERIAL NOT NULL, time_of_day DATETIME NOT NULL, "
                "requested_file VARCHAR(255), error_code INT NOT NULL, "
                "FOREIGN KEY (id) REFERENCES all_requests(id) );"
            )
        )

        db_conn.commit()
    return

def databaseStatistics():
    with pool.connect() as db_conn:
        print()
        print("================")

        req_count = db_conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM all_requests")).fetchone()[0]
        invalid_count = db_conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM invalid_requests")).fetchone()[0]

        print("Successful Requests:", req_count - invalid_count)
        print("Invalid Requests:", invalid_count)
        print()

        banned_count = db_conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM invalid_requests WHERE error_code = 400")).fetchone()[0]
        print("Requests from banned countries:", banned_count)

        m_count = db_conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM all_requests WHERE gender = 'Male'")).fetchone()[0]
        f_count = db_conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM all_requests WHERE gender = 'Female'")).fetchone()[0]
        print("Requests from male users:", m_count)
        print("Requests from female users:", f_count)

        top5_countries = db_conn.execute(sqlalchemy.text("SELECT country, COUNT(country) FROM all_requests GROUP BY country ORDER BY COUNT(country) DESC")).fetchmany(5)
        print("Top 5 Requesting Countries:", top5_countries)

        top_age = db_conn.execute(sqlalchemy.text("SELECT age FROM all_requests GROUP BY age ORDER BY COUNT(age) DESC")).fetchone()[0]
        print("Most requesting age group:", top_age)

        top_income = db_conn.execute(sqlalchemy.text("SELECT income FROM all_requests GROUP BY income ORDER BY COUNT(income) DESC")).fetchone()[0]
        print("Most requesting age group:", top_income)
        print("================")

    return


# Reset/Clear databases
resetDatabase()

# Fetch all entries in both databases
# fetchAllDatabase()

# Describe both databses
# describeDatabase()

# Perform statistics queries
# databaseStatistics()

connector.close()

