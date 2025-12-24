from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import sqlite3
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def is_strong_password(password):
    # 8+ characters
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    specials = set("!@#?")
    has_special = any(c in specials for c in password)

    # mixture of upper/lower, letters/numbers, and at least one special
    return has_upper and has_lower and has_letter and has_digit and has_special


def create_patient(tokens):
    # create_patient <username> <password>

    # Check 1: tokens must have exactly 3 items
    if len(tokens) != 3:
        print("Create patient failed")
        return

    username = tokens[1]
    password = tokens[2]

    # Check 2: whether the username already exists
    if username_exists_patient(username):
        print("Username taken, try again")
        return

    if not is_strong_password(password):
        print(
                'Create patient failed, please use a strong password (8+ char, at least one upper and one lower, '
                'at least one letter and one number, and at least one special character, from "!", "@", "#", "?")'
        )
        return

    # Generate salt and hash for password security
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # Create a Patient object
    patient = Patient(username, salt=salt, hash=hash)

    # Save the new patient into the database
    try:
        patient.save_to_db()
    except sqlite3.Error:
        print("Create patient failed")
        return
    except Exception:
        print("Create patient failed")
        return

    print("Created user", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    if not is_strong_password(password):
        print(
            'Create caregiver failed, please use a strong password (8+ char, at least one upper and one lower, '
            'at least one letter and one number, and at least one special character, from "!", "@", "#", "?")'
        )
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except sqlite3.Error as e:
        print("Failed to create user.", e)
        return
    except Exception as e:
        print("Failed to create user.", e)
        return
    print("Created user", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    # Check if the username already exists in the Patients table
    query = "SELECT Username FROM Patients WHERE Username = ?"
    try:
        cursor.execute(query, (username,))
        for _ in cursor:
            cm.close_connection()
            return True
    except sqlite3.Error:
        # If any database error happens, return True to avoid creating duplicates
        cm.close_connection()
        return True
    finally:
        cm.close_connection()
    return False


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(select_username, (username,))
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            cm.close_connection()
            return row['Username'] is not None
    except sqlite3.Error as e:
        print("Error occurred when checking username", e)
        cm.close_connection()
        return True
    except Exception as e:
        print("Error occurred when checking username", e)
        cm.close_connection()
        return True
    cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>

    global current_patient, current_caregiver

    # Check 1: no one should be logged in before this login
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in, try again")
        return

    # Check 2: tokens must include exactly 3 items
    if len(tokens) != 3:
        print("Login patient failed")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        # Retrieve patient info and verify password
        patient = Patient(username, password=password).get()
    except sqlite3.Error:
        print("Login patient failed")
        return
    except Exception:
        print("Login patient failed")
        return

    # Check if login succeeded
    if patient is None:
        print("Login patient failed")
    else:
        print("Logged in as", username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except sqlite3.Error as e:
        print("Login failed.", e)
        return
    except Exception as e:
        print("Login failed.", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # search_caregiver_schedule <date>

    global current_caregiver, current_patient

    # Check 1: someone must be logged in
    if current_caregiver is None and current_patient is None:
        print("Please login first")
        return

    # Check 2: command format
    if len(tokens) != 2:
        print("Please try again")
        return

    date = tokens[1]

    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Please try again")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        # Query available caregivers for the given date, ordered by username
        get_caregivers = """
            SELECT Username
            FROM Availabilities
            WHERE date(Time) = date(?)
            ORDER BY Username ASC
        """
        cursor.execute(get_caregivers, (date,))
        caregivers = [row["Username"] for row in cursor]

        print("Caregivers:")
        if len(caregivers) == 0:
            print("No caregivers available")
        else:
            for name in caregivers:
                print(name)

        # Query all vaccines and their remaining doses, ordered by name
        get_vaccines = """
            SELECT Name, Doses
            FROM Vaccines
            ORDER BY Name ASC
        """
        cursor.execute(get_vaccines)
        vaccines = cursor.fetchall()

        print("Vaccines:")
        if len(vaccines) == 0:
            print("No vaccines available")
        else:
            for row in vaccines:
                name = row["Name"]
                doses = row["Doses"]
                print(f"{name} {doses}")

    except sqlite3.Error:
        print("Please try again")
    except Exception:
        print("Please try again")
    finally:
        cm.close_connection()


def reserve(tokens):
    # reserve <date> <vaccine>

    global current_caregiver, current_patient

    # Check 1: someone must be logged in
    if current_caregiver is None and current_patient is None:
        print("Please login first")
        return

    # Check 2: the current user must be a patient
    if current_caregiver is not None:
        print("Please login as a patient")
        return

    # Check 3: command format
    if len(tokens) != 3:
        print("Please try again")
        return

    date = tokens[1]
    vaccine_name = tokens[2]

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        # 1) Find available caregivers for the given date (ordered alphabetically)
        get_caregivers = """
            SELECT Username
            FROM Availabilities
            WHERE date(Time) = date(?)
            ORDER BY Username ASC
        """
        cursor.execute(get_caregivers, (date,))
        caregivers = [row["Username"] for row in cursor]

        if len(caregivers) == 0:
            print("No caregiver is available")
            cm.close_connection()
            return

        chosen_caregiver = caregivers[0]

        # 2) Check vaccine doses
        get_doses = """
            SELECT Doses
            FROM Vaccines
            WHERE Name = ?
        """
        cursor.execute(get_doses, (vaccine_name,))
        row = cursor.fetchone()
        if row is None or row["Doses"] is None or row["Doses"] <= 0:
            print("Not enough available doses")
            cm.close_connection()
            return

        current_doses = row["Doses"]

        # 3) Determine next AppointmentID (start from 1, increment by 1)
        get_max_id = "SELECT MAX(AppointmentID) AS MaxID FROM Appointments"
        cursor.execute(get_max_id)
        row = cursor.fetchone()
        if row is None or row["MaxID"] is None:
            next_id = 1
        else:
            next_id = row["MaxID"] + 1

        # 4) Insert into Appointments
        insert_appointment = """
            INSERT INTO Appointments(AppointmentID, Time, CaregiverUsername, PatientUsername, VaccineName)
            VALUES (?, ?, ?, ?, ?)
        """
        patient_username = current_patient.get_username()
        cursor.execute(
            insert_appointment,
            (next_id, date, chosen_caregiver, patient_username, vaccine_name),
        )

        # 5) Remove caregiver availability for that date
        delete_availability = """
            DELETE FROM Availabilities
            WHERE date(Time) = date(?) AND Username = ?
        """
        cursor.execute(delete_availability, (date, chosen_caregiver))

        # 6) Decrease vaccine doses by 1
        update_vaccine = """
            UPDATE Vaccines
            SET Doses = ?
            WHERE Name = ?
        """
        cursor.execute(update_vaccine, (current_doses - 1, vaccine_name))

        # 7) Commit all changes
        conn.commit()

        # 8) Print confirmation
        print(f"Appointment ID {next_id}, Caregiver username {chosen_caregiver}")

    except sqlite3.Error:
        print("Please try again")
    except Exception:
        print("Please try again")
    finally:
        cm.close_connection()


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format yyyy-mm-dd
    date_tokens = date.split("-")
    year = int(date_tokens[0])
    month = int(date_tokens[1])
    day = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except sqlite3.Error as e:
        print("Upload Availability Failed", e)
        return
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    # cancel <appointment_id>
    global current_caregiver, current_patient

    # Must be logged in
    if current_caregiver is None and current_patient is None:
        print("Please login first")
        return

    # Format: cancel <appointment_id>
    if len(tokens) != 2:
        print("Please try again")
        return

    # Parse ID
    try:
        appt_id = int(tokens[1])
    except:
        print("Please try again")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        # Decide who is logged in
        if current_caregiver is not None:
            username = current_caregiver.get_username()
            query = """
                SELECT AppointmentID, Time, CaregiverUsername, PatientUsername, VaccineName
                FROM Appointments
                WHERE AppointmentID = ? AND CaregiverUsername = ?
            """
            cursor.execute(query, (appt_id, username))
        else:
            username = current_patient.get_username()
            query = """
                SELECT AppointmentID, Time, CaregiverUsername, PatientUsername, VaccineName
                FROM Appointments
                WHERE AppointmentID = ? AND PatientUsername = ?
            """
            cursor.execute(query, (appt_id, username))

        # Fetch appointment
        appt = cursor.fetchone()

        if appt is None:
            # Appointment does not exist OR does not belong to user
            print(f"Appointment ID {appt_id} does not exist")
            return

        time = appt["Time"]
        caregiver_username = appt["CaregiverUsername"]
        vaccine_name = appt["VaccineName"]

        # 1. Add caregiver availability back
        add_availability = """
            INSERT OR IGNORE INTO Availabilities(Time, Username)
            VALUES (?, ?)
        """
        cursor.execute(add_availability, (time, caregiver_username))

        # 2. Restore vaccine dose
        update_vaccine = """
            UPDATE Vaccines
            SET Doses = Doses + 1
            WHERE Name = ?
        """
        cursor.execute(update_vaccine, (vaccine_name,))

        # 3. Delete appointment
        delete_query = "DELETE FROM Appointments WHERE AppointmentID = ?"
        cursor.execute(delete_query, (appt_id,))

        conn.commit()

        print(f"Appointment ID {appt_id} has been successfully canceled")

    except sqlite3.Error:
        print("Please try again")
    except:
        print("Please try again")
    finally:
        cm.close_connection()


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except sqlite3.Error as e:
        print("Error occurred when adding doses", e)
        return
    except Exception as e:
        print("Error occurred when adding doses", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except sqlite3.Error as e:
            print("Error occurred when adding doses", e)
            return
        except Exception as e:
            print("Error occurred when adding doses", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except sqlite3.Error as e:
            print("Error occurred when adding doses", e)
            return
        except Exception as e:
            print("Error occurred when adding doses", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    # show_appointments

    global current_caregiver, current_patient

    # Check 1: some user must be logged in
    if current_caregiver is None and current_patient is None:
        print("Please login first")
        return

    # Command should be just one token: "show_appointments"
    if len(tokens) != 1:
        print("Please try again")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        # Case 1: caregiver is logged in
        if current_caregiver is not None:
            caregiver_username = current_caregiver.get_username()
            query = """
                SELECT AppointmentID, VaccineName, Time, PatientUsername
                FROM Appointments
                WHERE CaregiverUsername = ?
                ORDER BY AppointmentID ASC
            """
            cursor.execute(query, (caregiver_username,))
            rows = cursor.fetchall()

            if len(rows) == 0:
                print("No appointments scheduled")
                return

            for row in rows:
                appt_id = row["AppointmentID"]
                vaccine = row["VaccineName"]
                date = row["Time"]
                patient = row["PatientUsername"]
                print(f"{appt_id} {vaccine} {date} {patient}")

        # Case 2: patient is logged in
        else:
            patient_username = current_patient.get_username()
            query = """
                SELECT AppointmentID, VaccineName, Time, CaregiverUsername
                FROM Appointments
                WHERE PatientUsername = ?
                ORDER BY AppointmentID ASC
            """
            cursor.execute(query, (patient_username,))
            rows = cursor.fetchall()

            if len(rows) == 0:
                print("No appointments scheduled")
                return

            for row in rows:
                appt_id = row["AppointmentID"]
                vaccine = row["VaccineName"]
                date = row["Time"]
                caregiver = row["CaregiverUsername"]
                print(f"{appt_id} {vaccine} {date} {caregiver}")

    except sqlite3.Error:
        print("Please try again")
    except Exception:
        print("Please try again")
    finally:
        cm.close_connection()


def logout(tokens):
    # logout

    global current_caregiver, current_patient

    if len(tokens) != 1:
        print("Please try again")
        return

    # If no user is logged in
    if current_caregiver is None and current_patient is None:
        print("Please login first")
        return

    # Clear both caregiver and patient
    current_caregiver = None
    current_patient = None

    print("Successfully logged out")


def start():
    stop = False
    print("*** Please enter one of the following commands ***")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> quit")
    print()
    while not stop:
        print("> ", end='')
        try:
            response = input()
        except ValueError:
            print("Please try again!")
            break
        tokens = response.split()
        if len(tokens) == 0:
            print("Please try again!")
            continue
        operation = tokens[0].lower()

        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
