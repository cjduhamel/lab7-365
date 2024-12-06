import mysql.connector
from dotenv import load_dotenv

def get_connection():
    return mysql.connector.connect(
        user= db_user,
        password=db_password,
        host="mysql.labthreesixfive.com",
        database= db
    )

def setup_database():
    connection = get_connection()
    cursor = connection.cursor()

    ddl_statements = """
    CREATE TABLE IF NOT EXISTS lab7_rooms ( 
      RoomCode CHAR(5) PRIMARY KEY,
      RoomName VARCHAR(30) NOT NULL,
      Beds INT NOT NULL,
      bedType VARCHAR(8) NOT NULL,
      maxOcc INT NOT NULL,
      basePrice DECIMAL(6,2) NOT NULL,
      decor VARCHAR(20) NOT NULL,
      UNIQUE (RoomName)
    );

    CREATE TABLE IF NOT EXISTS lab7_reservations (
      CODE INT PRIMARY KEY,
      Room CHAR(5) NOT NULL,
      CheckIn DATE NOT NULL,
      Checkout DATE NOT NULL,
      Rate DECIMAL(6,2) NOT NULL,
      LastName VARCHAR(15) NOT NULL,
      FirstName VARCHAR(15) NOT NULL,
      Adults INT NOT NULL,
      Kids INT NOT NULL,
      FOREIGN KEY (Room) REFERENCES lab7_rooms (RoomCode)
    );
    """
    cursor.execute(ddl_statements, multi=True)
    connection.commit()
    connection.close()