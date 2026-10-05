import json
import os
import datetime

import json
import os

DATA_DIR = "data"

def load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
def save(filename, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

USERS_FILE = "users.json"
def register_user(username, password, role, name, dept=None, skills=None):
    users = load(USERS_FILE)
    if username in users:
        return (False, "Username already exists")
    users[username] = {
        "password": password,
        "role": role,
        "name": name,
        "dept": dept,
        "skills": skills if skills else {}
    }
    save(USERS_FILE, users)
    return (True, "Registered successfully")
def login_user(username, password):
    users = load(USERS_FILE)
    user = users.get(username)
    if user and user["password"] == password:
        return user
    return None
def check_eligibility(student_skills, required_skills):
    student_skills_lower = {skill.lower(): rating for skill, rating in student_skills.items()}
    for skill, min_rating in required_skills.items():
        skill_lower = skill.lower()
        if skill_lower not in student_skills_lower or student_skills_lower[skill_lower] < min_rating:
            return False
    return True

EVENTS_FILE = "events.json"
APPLICATIONS_FILE = "applications.json"

def clean_name(name):
    return name.strip()

def find_event(event_id):
    events = load(EVENTS_FILE)
    return events.get(event_id)

def create_event(event_id, name, description, organizer_username, required_skills, slots_needed):
    events = load(EVENTS_FILE)
    event_id = clean_name(event_id)
    name = clean_name(name)
    organizer_username = clean_name(organizer_username)
    if event_id == "":
        return False, "Event ID cannot be empty."
    if event_id in events:
        return False, "An event with this ID already exists."
    if name == "":
        return False, "Event name cannot be empty."
    if organizer_username == "":
        return False, "Organizer username cannot be empty."
    if not isinstance(required_skills, dict):
        return False, "Required skills must be a dictionary."
    if len(required_skills) == 0:
        return False, "At least one required skill is needed."
    if not isinstance(slots_needed, int) or slots_needed <= 0:
        return False, "Slots needed must be a positive number."
    event = {
        "name": name,
        "description": description.strip(),
        "organizer": organizer_username,
        "required_skills": required_skills,
        "slots_needed": slots_needed,
        "status": "open"
    }
    events[event_id] = event
    save(EVENTS_FILE, events)
    return True, "Event created successfully."

def view_events():
    events = load(EVENTS_FILE)
    print("\n===== AVAILABLE EVENTS =====")
    if len(events) == 0:
        print("No events are available.")
        return events
    for event_id, event in events.items():
        print(f"\n{event_id}. {event['name']}")
        print(f"   Description: {event['description']}")
        print(f"   Organizer: {event['organizer']}")
        print(f"   Required skills: {event['required_skills']}")
        print(f"   Slots needed: {event['slots_needed']}")
        print(f"   Status: {event['status']}")
    return events

def find_eligible_events(student_skills):
    events = load(EVENTS_FILE)
    results = []
    for event_id, event in events.items():
        if event["status"] != "open":
            continue
        if check_eligibility(student_skills, event["required_skills"]):
            results.append((event_id, event))
    return results

def view_matching_events(student_skills):
    matching_events = find_eligible_events(student_skills)
    print("\n===== MATCHING EVENTS =====")
    if len(matching_events) == 0:
        print("No matching events found.")
    else:
        for event_id, event in matching_events:
            print(f"- {event_id}: {event['name']}")
    return matching_events

def apply_to_event(event_id, username):
    events = load(EVENTS_FILE)
    applications = load(APPLICATIONS_FILE)
    username = clean_name(username)
    if event_id not in events:
        return False, "Event not found."
    event = events[event_id]
    if event["status"] != "open":
        return False, "This event is not open for applications."
    event_applications = applications.get(event_id, {})
    if username in event_applications:
        return False, "This student has already applied."
    accepted_count = 0
    for application in event_applications.values():
        if application["status"] == "accepted":
            accepted_count += 1
    if accepted_count >= event["slots_needed"]:
        return False, "This event is already full."
    applications.setdefault(event_id, {})[username] = {
        "status": "pending",
        "role": None,
        "hours": 0,
        "notes": ""
    }
    save(APPLICATIONS_FILE, applications)
    return True, "Applied successfully"

def view_applicants(event_id):
    events = load(EVENTS_FILE)
    applications = load(APPLICATIONS_FILE)
    print(f"\n===== APPLICANTS FOR {event_id} =====")
    if event_id not in events:
        print("Event not found.")
        return {}
    event_applications = applications.get(event_id, {})
    if len(event_applications) == 0:
        print("No applicants yet.")
        return {}
    for username, application in event_applications.items():
        print(f"- {username}: {application['status']}")
        if application["role"] is not None:
            print(f"  Role: {application['role']}")
        print(f"  Hours: {application['hours']}")
        if application["notes"] != "":
            print(f"  Notes: {application['notes']}")
    return event_applications

def update_application_status(event_id, username, new_status, role=None):
    events = load(EVENTS_FILE)
    applications = load(APPLICATIONS_FILE)
    username = clean_name(username)
    if event_id not in events:
        return False, "Event not found."
    if event_id not in applications:
        return False, "No applications found for this event."
    if username not in applications[event_id]:
        return False, "Application not found."
    application = applications[event_id][username]
    if application["status"] != "pending":
        return False, "This application has already been processed."
    if new_status not in ["accepted", "rejected"]:
        return False, "Invalid application status."
    if new_status == "accepted":
        accepted_count = 0
        for existing_application in applications[event_id].values():
            if existing_application["status"] == "accepted":
                accepted_count += 1
        if accepted_count >= events[event_id]["slots_needed"]:
            return False, "Cannot accept application. Event is full."
        application["status"] = "accepted"
        application["role"] = role
        message = "Application accepted successfully."
    else:
        application["status"] = "rejected"
        message = "Application rejected successfully."
    save(APPLICATIONS_FILE, applications)
    return True, message

import datetime
import os

EVENTS_FILE = "events.json"
APPLICATIONS_FILE = "applications.json"
USERS_FILE = "users.json"
CERT_FOLDER = "certificates"

def complete_event(event_id, contribution_updates):
    events = load(EVENTS_FILE)
    if event_id not in events:
        return False, "Event not found."
    applications = load(APPLICATIONS_FILE)
    for username in contribution_updates:
        if username not in applications.get(event_id, {}):
            return False, f"No application record found for '{username}'."
    for username, update in contribution_updates.items():
        applications[event_id][username]["hours"] = update["hours"]
        applications[event_id][username]["notes"] = update["notes"]
    events[event_id]["status"] = "completed"
    save(EVENTS_FILE, events)
    save(APPLICATIONS_FILE, applications)
    return True, "Event marked as completed."

def generate_certificate(event_id, username):
    events = load(EVENTS_FILE)
    if event_id not in events:
        return False, "Event not found."
    event = events[event_id]
    users = load(USERS_FILE)
    if username not in users:
        return False, "Student not found."
    student = users[username]
    applications = load(APPLICATIONS_FILE)
    if username not in applications.get(event_id, {}):
        return False, "Certificate cannot be generated. Student never applied to this event."
    app = applications[event_id][username]
    if event["status"] != "completed":
        return False, "Certificate cannot be generated. Event is not completed."
    if app["status"] != "accepted":
        return False, "Certificate cannot be generated. Student was not accepted."
    os.makedirs(CERT_FOLDER, exist_ok=True)
    today = datetime.date.today()
    letter_text = f"""
==========================================
        CERTIFICATE OF COMPLETION
==========================================
This certifies that {student["name"]} ({student["dept"]})
volunteered for "{event["name"]}" on {today}.
Role: {app["role"]}
Hours Contributed: {app["hours"]}
Notes: {app["notes"]}
Organizer: {event["organizer"]}
==========================================
"""
    path = os.path.join(CERT_FOLDER, f"{event_id}_{username}.txt")
    with open(path, "w") as f:
        f.write(letter_text)
    return True, path

def get_valid_choice(prompt, valid_options):
       while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print("Invalid choice, try again.")

def organizer_menu(username):
    while True:
        print("\n===== ORGANIZER MENU =====")
        print("1. Post Event")
        print("2. Review Applicants")
        print("3. Complete Event")
        print("4. Logout")
        choice = get_valid_choice("Enter choice: ", ["1", "2", "3", "4"])
        if choice == "1":
            print("\n===== POST EVENT =====")
            event_id = input("Enter event ID: ").strip()
            name = input("Enter event name: ").strip()
            description = input("Enter event description: ").strip()
            required_skills = {}
            print("\nEnter required skills.")
            print("Example: Python:3, CAD:2")
            print("Enter 'none' if no specific skills are required.")
            skills_input = input("Required skills: ").strip()
            if skills_input.lower() != "none" and skills_input != "":
                try:
                    skill_list = skills_input.split(",")
                    for skill_item in skill_list:
                        skill, rating = skill_item.split(":")
                        skill = skill.strip()
                        rating = int(rating.strip())
                        if rating < 0:
                            raise ValueError
                        required_skills[skill] = rating
                except ValueError:
                    print("Invalid skill format.")
                    print("Please use: Python:3, CAD:2")
                    continue
            try:
                slots_needed = int(input("Number of volunteer slots: ").strip())
                if slots_needed <= 0:
                    print("Number of slots must be greater than 0.")
                    continue
            except ValueError:
                print("Please enter a valid whole number.")
                continue
            result = create_event(
                event_id,
                name,
                description,
                username,
                required_skills,
                slots_needed
            )
            print(result[1])
        elif choice == "2":
            print("\n===== REVIEW APPLICANTS =====")
            all_events = load(
                EVENTS_FILE
            )
            all_applications = load(
                APPLICATIONS_FILE
            )
            organizer_events = []
            for event_id, event in all_events.items():
                if event.get("organizer") == username:
                    organizer_events.append(
                        (event_id, event)
                    )
            if not organizer_events:
                print("You have not posted any events.")
                continue
            print("\nYour events:")
            for event_id, event in organizer_events:
                print(
                    event_id,
                    "-",
                    event.get("name", "Unnamed Event"),
                    "[",
                    event.get("status", "unknown"),
                    "]"
                )
            event_id = input(
                "\nEnter event ID to review: "
            ).strip()
            if event_id not in all_events:
                print("Event does not exist.")
                continue
            if all_events[event_id].get("organizer") != username:
                print(
                    "You can only review applicants "
                    "for your own events."
                )
                continue
            event_applications = all_applications.get(
                event_id,
                {}
            )
            if not event_applications:
                print("No applicants for this event.")
                continue
            print("\n===== APPLICANTS =====")
            for applicant, application in event_applications.items():
                print("\nUsername:", applicant)
                print(
                    "Status:",
                    application.get("status")
                )
                print(
                    "Role:",
                    application.get("role")
                )
            applicant = input(
                "\nEnter applicant username to process: "
            ).strip()
            if applicant not in event_applications:
                print("Applicant not found.")
                continue
            if event_applications[applicant].get("status") != "pending":
                print(
                    "This application has already been processed."
                )
                continue
            decision = get_valid_choice(
                "Accept or reject? (a/r): ",
                ["a", "r"]
            )
            if decision == "a":
                role = input(
                    "Enter role for this volunteer: "
                ).strip()
                if role == "":
                    role = "Volunteer"
                result = update_application_status(
                    event_id,
                    applicant,
                    "accepted",
                    role
                )
            else:
                result = update_application_status(
                    event_id,
                    applicant,
                    "rejected"
                )
            print(result[1])
        elif choice == "3":
            print("\n===== COMPLETE EVENT =====")
            all_events = load(
                EVENTS_FILE
            )
            all_applications = load(
                APPLICATIONS_FILE
            )
            organizer_events = []
            for event_id, event in all_events.items():
                if event.get("organizer") == username:
                    organizer_events.append(
                        (event_id, event)
                    )
            if not organizer_events:
                print("You have not posted any events.")
                continue
            print("\nYour events:")
            for event_id, event in organizer_events:
                print(
                    event_id,
                    "-",
                    event.get("name", "Unnamed Event"),
                    "[",
                    event.get("status", "unknown"),
                    "]"
                )
            event_id = input(
                "\nEnter event ID to complete: "
            ).strip()
            if event_id not in all_events:
                print("Event does not exist.")
                continue
            if all_events[event_id].get("organizer") != username:
                print(
                    "You can only complete your own events."
                )
                continue
            if all_events[event_id].get("status") == "completed":
                print("This event is already completed.")
                continue
            event_applications = all_applications.get(
                event_id,
                {}
            )
            accepted_students = []
            for student, application in event_applications.items():
                if application.get("status") == "accepted":
                    accepted_students.append(student)
            if not accepted_students:
                print(
                    "There are no accepted volunteers "
                    "for this event."
                )
                continue
            contribution_updates = {}
            print(
                "\nEnter final contribution details "
                "for each accepted volunteer."
            )
            for student in accepted_students:
                print("\nVolunteer:", student)
                try:
                    hours = float(
                        input("Hours contributed: ").strip()
                    )
                    if hours < 0:
                        print(
                            "Hours cannot be negative."
                        )
                        contribution_updates = None
                        break
                except ValueError:
                    print(
                        "Please enter a valid number."
                    )
                    contribution_updates = None
                    break
                notes = input(
                    "Contribution notes: "
                ).strip()
                contribution_updates[student] = {
                    "hours": hours,
                    "notes": notes
                }
            if contribution_updates is None:
                continue
            result = complete_event(
                event_id,
                contribution_updates
            )
            print(result[1])
            if result[0]:
                print("\nGenerating certificates...")
                for student in accepted_students:
                    certificate_result = (
                        generate_certificate(
                            event_id,
                            student
                        )
                    )
                    print(certificate_result[1])
        elif choice == "4":
            print("Logging out...")
            break

def volunteer_menu(username, user_record):
    while True:
        print("\n===== VOLUNTEER MENU =====")
        print("1. View Eligible Events")
        print("2. Apply to an Event")
        print("3. View My Certificates")
        print("4. Logout")
        choice = get_valid_choice(
            "Enter choice: ",
            ["1", "2", "3", "4"]
        )
        if choice == "1":
            eligible_events = find_eligible_events(
                user_record.get("skills", {})
            )
            print("\n===== ELIGIBLE EVENTS =====")
            if not eligible_events:
                print("No eligible events found.")
            else:
                for event_id, event in eligible_events:
                    print("\nEvent ID:", event_id)
                    print(
                        "Name:",
                        event.get("name", "")
                    )
                    print(
                        "Description:",
                        event.get("description", "")
                    )
                    print(
                        "Organizer:",
                        event.get("organizer", "")
                    )
                    print(
                        "Required Skills:",
                        event.get("required_skills", {})
                    )
                    print(
                        "Slots:",
                        event.get("slots_needed", 0)
                    )
                    print(
                        "Status:",
                        event.get("status", "")
                    )
        elif choice == "2":
            print("\n===== APPLY TO AN EVENT =====")
            eligible_events = find_eligible_events(
                user_record.get("skills", {})
            )
            if not eligible_events:
                print("No eligible events found.")
                continue
            print("\nAvailable events:")
            for event_id, event in eligible_events:
                print(
                    event_id,
                    "-",
                    event.get("name", "Unnamed Event")
                )
            event_id = input(
                "\nEnter event ID to apply: "
            ).strip()
            eligible_ids = [
                event_id
                for event_id, event in eligible_events
            ]
            if event_id not in eligible_ids:
                print(
                    "Invalid event ID or you are not eligible "
                    "for this event."
                )
                continue
            result = apply_to_event(
                event_id,
                username
            )
            print(result[1])
        elif choice == "3":
            print("\n===== MY CERTIFICATES =====")
            certificate_folder = "certificates"
            if not os.path.exists(certificate_folder):
                print("No certificates found.")
            else:
                found = False
                for filename in os.listdir(
                    certificate_folder
                ):
                    if not filename.endswith(".txt"):
                        continue
                    if filename.endswith(
                        "_" + username + ".txt"
                    ):
                        print(filename)
                        found = True
                if not found:
                    print("No certificates found.")
        elif choice == "4":
            print("Logging out...")
            break

def main():
    while True:
        print("\n===== SKILLMATCH =====")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = get_valid_choice(
            "Enter choice: ",
            ["1", "2", "3"]
        )
        if choice == "1":
            print("\n===== REGISTER =====")
            username = input(
                "Enter username: "
            ).strip()
            password = input(
                "Enter password: "
            )
            print("\nChoose role:")
            print("1. Organizer")
            print("2. Student Volunteer")
            role_choice = get_valid_choice(
                "Enter choice: ",
                ["1", "2"]
            )
            name = input(
                "Enter full name: "
            ).strip()
            if role_choice == "1":
                result = register_user(
                    username,
                    password,
                    "Organizer",
                    name
                )
            else:
                dept = input(
                    "Enter department: "
                ).strip()
                skills = {}
                print(
                    "\nEnter your skills."
                )
                print(
                    "Example: Python:4, CAD:3"
                )
                print(
                    "Enter 'none' if you have no skills."
                )
                skills_input = input(
                    "Skills: "
                ).strip()
                if skills_input.lower() != "none" and skills_input != "":
                    try:
                        skill_list = skills_input.split(",")
                        for skill_item in skill_list:
                            skill, rating = (
                                skill_item.split(":")
                            )
                            skill = skill.strip()
                            rating = int(
                                rating.strip()
                            )
                            if rating < 0:
                                raise ValueError
                            skills[skill] = rating
                    except ValueError:
                        print(
                            "Invalid skill format."
                        )
                        print(
                            "Please use: "
                            "Python:4, CAD:3"
                        )
                        continue
                result = register_user(
                    username,
                    password,
                    "Student Volunteer",
                    name,
                    dept=dept,
                    skills=skills
                )
            print(result[1])
        elif choice == "2":
            print("\n===== LOGIN =====")
            username = input(
                "Enter username: "
            ).strip()
            password = input(
                "Enter password: "
            )
            user_record = login_user(
                username,
                password
            )
            if user_record is None:
                print(
                    "Invalid username or password."
                )
                continue
            print(
                "\nWelcome,",
                user_record.get("name", username)
            )
            role = user_record.get("role")
            if role == "Organizer":
                organizer_menu(username)
            elif role == "Student Volunteer":
                volunteer_menu(
                    username,
                    user_record
                )
            else:
                print(
                    "Unknown user role."
                )
        elif choice == "3":
            print("\nExiting SkillMatch...")
            break

if __name__ == "__main__":
    main()
