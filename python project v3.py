"""
events.py — Member 2's responsibility

Core Role:
- Event creation
- Event matching
- Volunteer applications
- Application status management

Uses:
- data_store.py for JSON file handling
- auth.py for student eligibility checking

Data shapes:

events = {
    "E01": {
        "name": "Tech Fest Setup",
        "description": "Stage sound and lighting setup",
        "organizer": "priya_organizer",
        "required_skills": {
            "Sound Systems": 2,
            "Electrical": 1
        },
        "slots_needed": 3,
        "status": "open"
    }
}

applications = {
    "E01": {
        "aditi101": {
            "status": "pending",
            "role": None,
            "hours": 0,
            "notes": ""
        }
    }
}
"""

import data_store
import auth


EVENTS_FILE = "events.json"
APPLICATIONS_FILE = "applications.json"


def clean_name(name):
    """Remove extra spaces from a name or username."""
    return name.strip()


def find_event(event_id):
    """Return an event by ID, or None if it does not exist."""

    events = data_store.load(EVENTS_FILE)

    return events.get(event_id)


def create_event(
    event_id,
    name,
    description,
    organizer_username,
    required_skills,
    slots_needed
):
    """
    Create a new event.

    New events always start with status "open".

    Returns:
        (True, message) if successful
        (False, reason) if unsuccessful
    """

    events = data_store.load(EVENTS_FILE)

    event_id = clean_name(event_id)
    name = clean_name(name)
    organizer_username = clean_name(organizer_username)

    # Check event ID
    if event_id == "":
        return False, "Event ID cannot be empty."

    if event_id in events:
        return False, "An event with this ID already exists."

    # Check event name
    if name == "":
        return False, "Event name cannot be empty."

    # Check organizer
    if organizer_username == "":
        return False, "Organizer username cannot be empty."

    # Check required skills
    if not isinstance(required_skills, dict):
        return False, "Required skills must be a dictionary."

    if len(required_skills) == 0:
        return False, "At least one required skill is needed."

    # Check slot count
    if not isinstance(slots_needed, int) or slots_needed <= 0:
        return False, "Slots needed must be a positive number."

    # Create event
    event = {
        "name": name,
        "description": description.strip(),
        "organizer": organizer_username,
        "required_skills": required_skills,
        "slots_needed": slots_needed,
        "status": "open"
    }

    events[event_id] = event

    data_store.save(EVENTS_FILE, events)

    return True, "Event created successfully."


def view_events():
    """Display all events and return the event dictionary."""

    events = data_store.load(EVENTS_FILE)

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
    """
    Find all open events for which the student is eligible.

    Eligibility is checked using auth.check_eligibility().

    Returns:
        List of (event_id, event_dict) tuples.
    """

    events = data_store.load(EVENTS_FILE)

    results = []

    for event_id, event in events.items():

        # Only open events can be matched
        if event["status"] != "open":
            continue

        # Check student's skills
        if auth.check_eligibility(
            student_skills,
            event["required_skills"]
        ):
            results.append((event_id, event))

    return results


def view_matching_events(student_skills):
    """Display events that match a student's skills."""

    matching_events = find_eligible_events(student_skills)

    print("\n===== MATCHING EVENTS =====")

    if len(matching_events) == 0:
        print("No matching events found.")
    else:
        for event_id, event in matching_events:
            print(f"- {event_id}: {event['name']}")

    return matching_events


def apply_to_event(event_id, username):
    """
    Submit a pending application for a student.

    Checks:
    1. Event exists.
    2. Event is open.
    3. Student has not already applied.
    4. Event still has an available slot.

    Returns:
        (True, "Applied successfully")
        or
        (False, reason)
    """

    events = data_store.load(EVENTS_FILE)
    applications = data_store.load(APPLICATIONS_FILE)

    username = clean_name(username)

    # Check event exists
    if event_id not in events:
        return False, "Event not found."

    event = events[event_id]

    # Check event status
    if event["status"] != "open":
        return False, "This event is not open for applications."

    # Get applications for this event
    event_applications = applications.get(event_id, {})

    # Check duplicate application
    if username in event_applications:
        return False, "This student has already applied."

    # Count accepted applicants
    accepted_count = 0

    for application in event_applications.values():

        if application["status"] == "accepted":
            accepted_count += 1

    # Check available slots
    if accepted_count >= event["slots_needed"]:
        return False, "This event is already full."

    # Create application
    applications.setdefault(event_id, {})[username] = {
        "status": "pending",
        "role": None,
        "hours": 0,
        "notes": ""
    }

    # Save application
    data_store.save(APPLICATIONS_FILE, applications)

    return True, "Applied successfully"


def view_applicants(event_id):
    """Display all applicants for an event."""

    events = data_store.load(EVENTS_FILE)
    applications = data_store.load(APPLICATIONS_FILE)

    print(f"\n===== APPLICANTS FOR {event_id} =====")

    if event_id not in events:
        print("Event not found.")
        return {}

    event_applications = applications.get(event_id, {})

    if len(event_applications) == 0:
        print("No applicants yet.")
        return {}

    for username, application in event_applications.items():

        print(
            f"- {username}: "
            f"{application['status']}"
        )

        if application["role"] is not None:
            print(f"  Role: {application['role']}")

        print(f"  Hours: {application['hours']}")

        if application["notes"] != "":
            print(f"  Notes: {application['notes']}")

    return event_applications


def update_application_status(
    event_id,
    username,
    new_status,
    role=None
):
    """
    Accept or reject a pending application.

    Accepted applications also store the applicant's role.

    Valid status changes:

        pending -> accepted
        pending -> rejected

    Returns:
        (True, message)
        or
        (False, reason)
    """

    events = data_store.load(EVENTS_FILE)
    applications = data_store.load(APPLICATIONS_FILE)

    username = clean_name(username)

    # Check event
    if event_id not in events:
        return False, "Event not found."

    # Check applications
    if event_id not in applications:
        return False, "No applications found for this event."

    if username not in applications[event_id]:
        return False, "Application not found."

    application = applications[event_id][username]

    # Only pending applications can be processed
    if application["status"] != "pending":
        return False, "This application has already been processed."

    # Check status value
    if new_status not in ["accepted", "rejected"]:
        return False, "Invalid application status."

    # Accept application
    if new_status == "accepted":

        accepted_count = 0

        for existing_application in applications[event_id].values():

            if existing_application["status"] == "accepted":
                accepted_count += 1

        # Prevent exceeding event capacity
        if accepted_count >= events[event_id]["slots_needed"]:
            return False, "Cannot accept application. Event is full."

        application["status"] = "accepted"
        application["role"] = role

        message = "Application accepted successfully."

    # Reject application
    else:

        application["status"] = "rejected"

        message = "Application rejected successfully."

    data_store.save(APPLICATIONS_FILE, applications)

    return True, message


if __name__ == "__main__":

    print("===== SkillMatch Events Module =====")

    # Example event data
    success, message = create_event(
        "E01",
        "College Tech Fest",
        "Annual technical festival",
        "priya_organizer",
        {
            "Python": 3,
            "Communication": 2
        },
        3
    )

    print(message)

    # Display events
    view_events()

    # Example student skills
    student_skills = {
        "Python": 4,
        "Communication": 3
    }

    # Find matching events
    view_matching_events(student_skills)

    # Submit application
    success, message = apply_to_event(
        "E01",
        "aditi101"
    )

    print(message)

    # Display applicants
    view_applicants("E01")

    # Accept application
    success, message = update_application_status(
        "E01",
        "aditi101",
        "accepted",
        role="Technical Volunteer"
    )

    print(message)

    # Display updated applicants
    view_applicants("E01")