from decimal import Decimal

from database import get_connection
from datetime import datetime, timedelta
import warnings
import pandas as pd
import datetime

# Suppress specific warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")
warnings.filterwarnings("ignore", message="Downcasting object dtype arrays on")

def rooms_and_rates():
    #FR1
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    WITH 
    RoomPopularity AS (
        SELECT
            r.RoomCode,
            COUNT(res.CheckIn) * 1.0 / 180 AS PopularityScore
        FROM lab7_rooms r
        LEFT JOIN lab7_reservations res ON r.RoomCode = res.Room
        WHERE DATE(res.CheckOut) >= DATE_SUB(CURDATE(), INTERVAL 180 DAY) 
          AND DATE(res.CheckIn) <= CURDATE()
        GROUP BY r.RoomCode
    ),
    NextAvailable AS (
        SELECT
            r.RoomCode,
            MIN(res.CheckOut) AS NextCheckIn
        FROM lab7_rooms r
        LEFT JOIN lab7_reservations res ON r.RoomCode = res.Room
        WHERE DATE(res.CheckOut) > CURDATE()
        GROUP BY r.RoomCode
    ),
    RecentStay AS (
        SELECT
            r.RoomCode,
            MAX(res.CheckOut) AS LastCheckOut,
            DATEDIFF(MAX(res.CheckOut), MAX(res.CheckIn)) AS StayLength
        FROM lab7_rooms r
        LEFT JOIN lab7_reservations res ON r.RoomCode = res.Room
        WHERE DATE(res.CheckOut) <= CURDATE()
        GROUP BY r.RoomCode
    )
    SELECT
        r.*,
        COALESCE(ROUND(p.PopularityScore, 2), 0.00) AS PopularityScore,
        COALESCE(na.NextCheckIn, 'Available Now') AS NextCheckIn,
        COALESCE(rs.StayLength, 0) AS RecentStayLength,
        COALESCE(rs.LastCheckOut, 'Never Occupied') AS LastCheckOut
    FROM lab7_rooms r
    LEFT JOIN RoomPopularity p ON r.RoomCode = p.RoomCode
    LEFT JOIN NextAvailable na ON r.RoomCode = na.RoomCode
    LEFT JOIN RecentStay rs ON r.RoomCode = rs.RoomCode
    ORDER BY PopularityScore DESC;
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results


def find_available_rooms(start_date, end_date, room_code=None, bed_type=None, guest_count=0):
    #FR2
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    #finding rooms
    query = """
    SELECT r.RoomCode, r.RoomName, r.Beds, r.bedType, r.maxOcc, r.basePrice, r.decor
    FROM lab7_rooms r
    LEFT JOIN lab7_reservations res
    ON r.RoomCode = res.Room
    AND (
        (res.CheckIn <= %s AND res.Checkout > %s) OR  -- Overlapping reservations
        (res.CheckIn < %s AND res.Checkout >= %s) OR
        (res.CheckIn >= %s AND res.Checkout <= %s)
    )
    WHERE res.Room IS NULL  -- Only show rooms without overlapping reservations
    """

    # Add filters
    filters = [start_date, start_date, end_date, end_date, start_date, end_date]
    if room_code and room_code != "Any":
        query += " AND r.RoomCode = %s"
        filters.append(room_code)
    if bed_type and bed_type != "Any":
        query += " AND r.bedType = %s"
        filters.append(bed_type)

    cursor.execute(query, filters)
    results = cursor.fetchall()

    available_rooms = [room for room in results if guest_count <= room["maxOcc"]]

    cursor.close()
    connection.close()

    if available_rooms:
        return available_rooms
    return None


def alternative_rooms(start_date, end_date, guest_count, room_code=None, bed_type=None, range_days=30, limit=5):
    # FR2
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # adjust the date range by a month
    relaxed_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=range_days)).strftime("%Y-%m-%d")
    relaxed_end_date = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=range_days)).strftime("%Y-%m-%d")

    query = """
        SELECT DISTINCT r.RoomCode, r.RoomName, r.Beds, r.bedType, r.maxOcc, r.basePrice, r.decor
        FROM lab7_rooms r
        LEFT JOIN lab7_reservations res
        ON r.RoomCode = res.Room
        AND (
            (res.CheckIn <= %s AND res.Checkout > %s) OR  -- Overlapping reservations
            (res.CheckIn < %s AND res.Checkout >= %s) OR
            (res.CheckIn >= %s AND res.Checkout <= %s)
        )
        WHERE res.Room IS NULL  -- Only show rooms without overlapping reservations
        """
    filters = [relaxed_start_date, relaxed_start_date, relaxed_end_date, relaxed_end_date, relaxed_start_date,
               relaxed_end_date]

    if bed_type and bed_type != "Any":
        query += " AND r.bedType = %s"
        filters.append(bed_type)

    query += " AND r.maxOcc >= %s LIMIT %s"
    filters.extend([guest_count, limit])

    cursor.execute(query, filters)
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results


def total_cost(start_date, end_date, base_rate):
    # FR2
    if not isinstance(base_rate, Decimal):
        base_rate = Decimal(base_rate)

    weekdays = 0
    weekends = 0

    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    while current_date < end_date:
        if current_date.weekday() < 5:  # Weekday
            weekdays += 1
        else:  # Weekend
            weekends += 1
        current_date += timedelta(days=1)

    weekday_cost = weekdays * base_rate
    weekend_cost = weekends * base_rate * Decimal(1.1)
    return round(weekday_cost + weekend_cost, 2)


def book_reservation(first_name, last_name, room_code, start_date, end_date, adults, kids, total_cost):
    # FR2
    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO lab7_reservations (Room, CheckIn, Checkout, Rate, LastName, FirstName, Adults, Kids)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (room_code, start_date, end_date, total_cost, last_name, first_name, adults, kids))
    cursor.close()
    connection.close()


def search_reservations(vals : dict):
    #FR4
    connection = get_connection()

    for key in vals:
        if key == "start_date":
            if vals[key]:
                vals[key] = "CheckIn >= '" + vals[key] + "' AND"
            else:
                vals[key] = ""
        elif key == "end_date":
            if vals[key]:
                vals[key] = "CheckOut <= '" + vals[key] + "' AND"
            else:
                vals[key] = ""
        else:
            if not vals[key]:
                vals[key] = "%"

    query = """
        SELECT CODE, Room, RoomName, CheckIn, CheckOut, Rate, LastName, FirstName, Adults, Kids FROM lab7_reservations
            INNER JOIN lab7_rooms ON lab7_reservations.Room = lab7_rooms.RoomCode
        WHERE 
            FirstName LIKE "%s" AND 
            LastName LIKE "%s" AND
            %s
            %s
            Room LIKE "%s" AND
            CODE LIKE "%s"
        """ % (vals["first_name"], vals["last_name"], vals["start_date"], vals["end_date"], vals["room_code"], vals["reservation_code"])
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

def reservation_exists(res_code):
    connection = get_connection()
    
    query = "SELECT * FROM lab7_reservations WHERE CODE = %s" % res_code

    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

def cancel_reservation(res_code):
    connection = get_connection()
    cursor = connection.cursor()
    
    query = "DELETE FROM lab7_reservations WHERE CODE = %s" % res_code
    cursor.execute(query)
    cursor.close()
    connection.close()

def get_revenue():
    connection = get_connection()
    current_year = datetime.datetime.now().year
    print("\n\nCurrent Year: ", current_year)
    query = """
        WITH room_month AS (
            SELECT RoomCode, RoomName, CODE, CheckIn, CheckOut, MONTH(CheckIn), 
                   ROUND(DATEDIFF(LEAST(CheckOut, "{0}-{1}-{7}"), GREATEST(CheckIn, "{2}-{3}-01")) * Rate) AS DollarRevenue
            FROM lab7_rooms AS rm
            INNER JOIN lab7_reservations AS rs ON Room = RoomCode
            WHERE (YEAR(CheckIn) = YEAR(CURRENT_DATE) OR YEAR(CheckOut) = YEAR(CURRENT_DATE))
              AND (MONTH(CheckIn) = {4} OR MONTH(CheckOut) = {5})
            ORDER BY CheckIn
        )
        
        SELECT RoomCode, RoomName, SUM(DollarRevenue) as Revenue{6}
        FROM room_month
        GROUP BY RoomCode, RoomName
    """

    df = pd.read_sql_query("SELECT RoomCode, RoomName FROM lab7_rooms", connection)

    # Loop through months
    for i in range(1, 13):
        i_0 = i
        next_month = i + 1
        if i < 10:
            i_0 = '0' + str(i)
        if next_month < 10:
            next_month = '0' + str(next_month)
        next_year = current_year

        day = "01"
        
        if i == 12:
            next_month = '12'
            next_year = current_year
            day = "31"
            

        
        formatted_query = query.format(next_year, next_month, current_year, i_0, i, i, i, day) 
        print("\n\nQuery for Month: ", i)
        print(formatted_query)
        result_df = pd.read_sql_query(formatted_query, connection)
        df = df.merge(result_df, how='outer', on=['RoomCode', 'RoomName'])

    # Close the connection once after all queries are executed
    connection.close()

    #format all revenue columns to be integers (not the first two columns)
    df = df.fillna(0)
    for i in range(2, 14):
        df.iloc[:, i] = df.iloc[:, i].astype(int)
    df['Total'] = df.sum(axis=1, numeric_only=True)

    #add row at end with column totals
    df.loc['Total'] = df.sum(numeric_only=True, axis=0)

    return df

#rev = get_revenue()
#print(rev)
#rev.to_csv("revenue.csv", index=False)
