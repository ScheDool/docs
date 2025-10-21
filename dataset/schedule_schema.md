
# Schedule Schema Documentation

This document describes the unified **in-memory schedule schema** used to represent teaching slots and their assignments across different teaching types.

---

## Norms & Definitions
- **Class**
  Represents a group of students belonging to the same homeroom.
  Identified by `class_id` written in format `<grade>/<section>`.
  - Example: "1/1" = Grade 1, Section 1
- **Subject**
  Academic subject being taught (e.g., Math, Science, Language).
  Identified by `class_id` written in format `c00000` 1 single character (represent the department) and 5 digits.
  - Example "M10010": Basic Math 1
- **Teacher**
  Person responsible for delivering lessons.
  Identified by `teacher_id` (e.g., "T001", "T002").
- **Room**
  Physical location where the lesson happens.
  Identified by `room_id` (e.g., "1001", "COM1", "GYM").
- **Period**
  The smallest unit of time in the school timetable, representing one teaching session.
  Defined by school (e.g. Period 1 = 08.30 - 09.20, Period 2 = 09.20 - 10.10).
  Break, Lunch, Homeroom, etc. may or may not inlcluded in the timetable, depending on school.
- **Slot**
  Unique period in the timetable defined by day and period.
  Idenified by `slot_id` wrttien in format `<day>_<period>`.
  - Example: "MON_1" = Monday Period 1
- **Group**
  A teaching subgroup within a slot (used in split or elective cases). Each group has its own teacher(s), room(s), and sometimes subset of classes.
- **Constraints**
  Optional rules for scheduling, such as:
  TEAM: multiple teachers in the same session
  MAX2DAY: subject limited to 2 periods per day
  LAB: must be in a lab room

---

## General Structure

Each schedule entry is represented as a **slot**.
Each `Class`, `Teacher`, and `Room` can be assigned to only **one subject** in a given slot. These entities are generally linked together within the schedule.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "DAY_PERIOD",
  "subject_id": "SUBJECT",
  "teaching_type": "TYPE",
  "class_ids": [],
  "groups": [
    {
      "group_id": 1,
      "class_ids": [],
      "teacher_ids": [],
      "room_ids": [],
      "constraint_ids": []
    }
  ]
}
```

### Field Descriptions

- **schedule_id**: (BIGINT? | UUID?) Unique identifier of schedule.
- **slot_id**: (String) Slot identifier, containing `slot_id`.
- **subject_id**: (String) Subject identifier, containting `subject_id`.
- **teaching_type**: (String) Defines the teaching style. One of:
  - `Standard`
  - `Team`
  - `Split`
  - `Multi-Class`
  - `Multi-Class Team`
  - `Subgroup`
  - `Mix` (Future case)
- **class_ids**: (Array of Strings) Contain `class_id` of all participating classes in this slot.
- **groups**: (Array of Objects) List of teaching groups with details.
  - **group_id**: (Integer) Unique group identifier within the slot (aka group number).
  - **class_ids**: (Array of Strings) Contain `class_id` of class(es) covered by each group (can be empty if split subgroup or student-choice subgroup).
  - **teacher_ids**: (Array of Strings) Contain `teacher_id` of assigned teacher(s) to each group.
  - **room_ids**: (Strings) Contain `room_id` of Assigned room(s) to each group.
  - **constraints**: Optional scheduling constraints (e.g., `TEAM`, `MAX2DAY`).

---

## Teaching Types

### 1. Standard Teaching
One class, one teacher, one room.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_1",
  "subject_id": "MATH1",
  "teaching_type": "Standard",
  "class_ids": ["/1"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": ["/1"],
      "teacher_ids": ["TA"],
      "room_ids": ["R101"],
      "constraints": []
    }
  ]
}
```

### 2. Team Teaching
One class, multiple teachers, one room.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_1",
  "subject_id": "SCI",
  "teaching_type": "Team",
  "class_ids": ["/1"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": ["/1"],
      "teacher_ids": ["TA", "TB"],
      "room_ids": ["Lab1"],
      "constraints": ["TEAM"]
    }
  ]
}
```

### 3. Split Teaching
One class, divided into subgroups.

- `class_ids` at slot-level lists the full class.
- `class_ids` at group-level is empty to indicate subgroup split.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_1",
  "subject_id": "PE",
  "teaching_type": "Split",
  "class_ids": ["/1"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": [],
      "teacher_ids": ["TA"],
      "room_ids": ["Gym1"],
      "constraints": []
    },
    {
      "group_id": 2,
      "class_ids": [],
      "teacher_ids": ["TB"],
      "room_ids": ["Gym2"],
      "constraints": []
    }
  ]
}
```

### 4. Multi-Class Teaching
Multiple classes, one teacher, one room.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_2",
  "subject_id": "HIS",
  "teaching_type": "Multi-Class",
  "class_ids": ["/1", "/2", "/3"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": ["/1", "/2", "/3"],
      "teacher_ids": ["TA"],
      "room_ids": ["R201"],
      "constraints": []
    }
  ]
}
```

### 5. Multi-Class Team Teaching
Multiple classes, multiple teachers, one room.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_2",
  "subject_id": "SCI",
  "teaching_type": "Multi-Class Team",
  "class_ids": ["/1", "/2", "/3"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": ["/1", "/2", "/3"],
      "teacher_ids": ["TA", "TB"],
      "room_ids": ["Lab3"],
      "constraints": ["TEAM"]
    }
  ]
}
```

### 6. Subgroup Teaching

#### Case 6.1: Class-based Subgroups
Each class split into separate groups, each with its own teacher/room.

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_3",
  "subject_id": "ART",
  "teaching_type": "Subgroup",
  "class_ids": ["/1", "/2", "/3"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": ["/1"],
      "teacher_ids": ["TA"],
      "room_ids": ["Room1"],
      "constraints": []
    },
    {
      "group_id": 2,
      "class_ids": ["/2"],
      "teacher_ids": ["TB"],
      "room_ids": ["Room2"],
      "constraints": []
    },
    {
      "group_id": 3,
      "class_ids": ["/3"],
      "teacher_ids": ["TC"],
      "room_ids": ["Room3"],
      "constraints": []
    }
  ]
}
```

#### Case 6.2: Student-Choice Subgroups
Subgroups independent of class_id (e.g., language choices).

```json
{
  "schedule_id": "SCHEDULE_ID",
  "slot_id": "MON_3",
  "subject_id": "LANG",
  "teaching_type": "Subgroup",
  "class_ids": ["/1", "/2", "/3"],
  "groups": [
    {
      "group_id": 1,
      "class_ids": [],
      "teacher_ids": ["T_JPN"],
      "room_ids": ["Room_JPN"],
      "constraints": []
    },
    {
      "group_id": 2,
      "class_ids": [],
      "teacher_ids": ["T_KOR"],
      "room_ids": ["Room_KOR"],
      "constraints": []
    },
    {
      "group_id": 3,
      "class_ids": [],
      "teacher_ids": ["T_CHN"],
      "room_ids": ["Room_CHN"],
      "constraints": []
    }
  ]
}
```

---

