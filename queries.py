from database import get_connection
from datetime import datetime, timedelta

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

    # filters for room code and bed type
    if room_code and room_code != "Any":
        query += " AND r.RoomCode = %s"
        filters.append(room_code)
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
    weekend_cost = weekends * base_rate * 1.1
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

