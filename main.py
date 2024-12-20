from database import setup_database
from queries import *
import pandas as pd

def display_rooms():
    # FR1
    results = rooms_and_rates()
    print(f"{'RoomCode':<10} {'RoomName':<20} {'Popularity':<10} {'NextCheckIn':<15} {'RecentStayLength':<15} {'LastCheckOut':<15}")
    print("-" * 85)
    for row in results:
        print(f"{row['RoomCode']:<10} {row['RoomName']:<20} {row['PopularityScore']:<10.2f} {row['NextCheckIn']:<15} {row['RecentStayLength']:<15} {row['LastCheckOut']:<15}")


def reservations():
    # FR2
    print("Enter your reservation details.")
    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    room_code = input("Room Code (or 'Any'): ")
    bed_type = input("Bed Type (or 'Any'): ")
    start_date = input("Begin Date (YYYY-MM-DD): ")
    end_date = input("End Date (YYYY-MM-DD): ")
    adults = int(input("Number of Adults: "))
    kids = int(input("Number of Children: "))
    guest_count = adults + kids

    # Check room availability
    available_rooms = find_available_rooms(start_date, end_date, room_code, bed_type, guest_count)
    if not available_rooms:
        print("\nNo exact rooms found. Here are alternatives within a month of the dates you requested:")
        suggestions = alternative_rooms(start_date, end_date, guest_count, room_code, bed_type)
        if not suggestions:
            print("Unfortunately, no rooms are available.")
            return
        print("\nAlternative Rooms:")
        for i, room in enumerate(suggestions, 1):
            print(
                f"{i}. RoomCode: {room['RoomCode']}, Name: {room['RoomName']}, Bed Type: {room['bedType']}, Base Price: {room['basePrice']}")
        choice = input("\nEnter option number to book, or 'Cancel' to exit: ").strip()
        if choice.lower() == "cancel":
            print("Reservation cancelled.")
            return
        selected_room = suggestions[int(choice) - 1]
        cost = total_cost(start_date, end_date, selected_room["basePrice"])

        # Confirm booking
        print("\nBooking Confirmation:")
        print(f"Name: {first_name} {last_name}")
        print(f"Room: {selected_room['RoomCode']} ({selected_room['RoomName']}), Bed Type: {selected_room['bedType']}")
        print(f"Dates: {start_date} to {end_date}")
        print(f"Adults: {adults}, Children: {kids}")
        print(f"Total Cost: ${cost}")

        confirm = input("\nConfirm booking? (yes/no): ")
        if confirm.lower() == "yes":
            book_reservation(first_name, last_name, selected_room["RoomCode"], start_date, end_date, adults, kids,
                             cost)
            print("Reservation successfully booked!")
        else:
            print("Ok, have a good day.")


    else:
        # Display available rooms
        print("\nAvailable Rooms:")
        for i, room in enumerate(available_rooms, 1):
            print(
                f"{i}. RoomCode: {room['RoomCode']}, Name: {room['RoomName']}, Bed Type: {room['bedType']}, Base Price: {room['basePrice']}")

        # Prompt user to book
        choice = input("\nEnter option number to book, or 'Cancel' to exit: ")
        if choice.lower() == "cancel":
            print("Reservation cancelled.")
            return

        selected_room = available_rooms[int(choice) - 1]
        cost = total_cost(start_date, end_date, selected_room["basePrice"])

        # Confirm booking
        print("\nBooking Confirmation:")
        print(f"Name: {first_name} {last_name}")
        print(f"Room: {selected_room['RoomCode']} ({selected_room['RoomName']}), Bed Type: {selected_room['bedType']}")
        print(f"Dates: {start_date} to {end_date}")
        print(f"Adults: {adults}, Children: {kids}")
        print(f"Total Cost: ${cost}")

        confirm = input("\nConfirm booking? (yes/no): ")
        if confirm.lower() == "yes":
            book_reservation(first_name, last_name, selected_room["RoomCode"], start_date, end_date, adults, kids,
                             cost)
            print("Reservation successfully booked!")
        else:
            print("Ok, have a good day.")


def reservation_cancel():
    # FR3
    print("Reservation Cancellation\n")
    print("Please enter your reservation code to cancel your reservation.")

    reservation_code = input("Reservation Code: ")
    res = pd.DataFrame()
    try:
        res = reservation_exists(reservation_code)
    except:
        print("\nError occurred while searching for reservation.")
        return

    if not res.empty:
        print("Reservation found.")
        print("Reservation Details:")
        print(res.to_string(index=False))
        confirm = input("Are you sure you want to cancel this reservation? (yes/no): ")
        if confirm.lower() == "yes":
            cancel_reservation(reservation_code)
            print("Reservation successfully cancelled.")
        else:
            print("Ok, have a good day.")
    else:
        print("Reservation not found.")
        


def detailed_reservation():
    # FR4
    print("Welcome to the Reservation Search System\n")
    print("Enter your Search Criteria, leave a field blank to skip it\n")

    vals = {}
    vals["first_name"] = input("First Name: ")
    vals["last_name"] = input("Last Name: ")
    vals["start_date"] = input("Start Date (YYYY-MM-DD): ")
    vals["end_date"] = input("End Date (YYYY-MM-DD): ")
    vals["room_code"] = input("Room Code: ")
    vals["reservation_code"] = input("Reservation Code: ")

    results : pd.DataFrame = search_reservations(vals)

    print("\nSearch Results:")
    print(results.to_string(index=False))


def revenue():
    # FR5
    revenue = get_revenue()
    #print the dataframe
    print(revenue.to_string(index=False))



def main():
    setup_database()
    user_input = input("Enter command: ").strip()
    if user_input == "1":
        display_rooms()
    elif user_input == "2":
        reservations()
    elif user_input == "3":
        reservation_cancel()
    elif user_input == "4":
        detailed_reservation()
    elif user_input == "5":
        revenue()
    else:
        print("bye")
    


if __name__ == "__main__":
    main()
