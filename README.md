# Electronic Voting System

This repository contains a lightweight electronic voting system built with **FastAPI**, **Jinja2Templates**, and **Tailwind CSS**, designed to simplify the creation and management of secure online votings. Below is a high-level overview of the features and workflow.

## Key Features

- **FastAPI Backend**  
  - RESTful endpoints for creating and managing votings.  
  - Uses Pydantic models for validating input data (e.g., title, options, entity, logo).  
  - Encrypts voting files on disk to ensure confidentiality.

- **File-Based Persistence with Encryption**  
  - Each voting is saved as an encrypted file.  
  - The admin receives a unique **admin key** to decrypt and manage the voting.  
  - Uses the `cryptography` package to protect sensitive information.

- **Token-Based Voting**  
  - Each voter is assigned a unique token, which provides access to cast exactly one vote.  
  - Tokens are stored in a separate JSON index (`tokens_index.json`) to map them to a specific voting ID and key.

- **Jinja2 Templates**  
  - **`base.html`** defines the main layout (header, footer, etc.).  
  - Separate pages for each step:
    - `create_form.html`: Simple form to create a new voting (including entity name, logo, title, and options).
    - `votacion_creada.html`: Shows the result of creating a new voting and provides the admin key.
    - `admin_panel.html`: Displays voting details, options, and a form to add or remove voters.
    - `votar.html`: Voters see the title, entity, and logo, then select an option to submit.
    - `resultado_voto.html`: Confirms if the vote succeeded or if an error occurred.
    - `audit_logs.html`: Displays a chronological list of all actions (vote creation, adding voters, removing voters, etc.) with timestamps.

- **Audit Logs**  
  - Logs each action (e.g., create voting, add voter, cast vote, remove voter) with a timestamp.  
  - Enables admins to see a history of all modifications and votes via `audit_logs.html`.

- **Friendly Error Pages**  
  - Custom exception handlers can return an HTML page instead of raw JSON for errors like 404 (Not Found) or 405 (Method Not Allowed).

- **Additional Features**  
  - Simple roles: **Admin** (creates and manages the voting) and **Voters** (cast votes).  
  - Prevents multiple votes with the same token (once a voter has cast a vote, `ya_voto` is set to `true`).

## Typical Workflow

1. **Create Voting**  
   - A user opens the root path (`"/"`) to fill a simple form: title, options, entity, logo.  
   - The backend generates a random `voting_id` and a secret key.  
   - The user (admin) receives these details.

2. **Admin Panel**  
   - Accessed via `/admin_panel?voting_id={...}&key={...}`.  
   - Shows the list of voting options and allows adding or removing voters.  
   - Each voter receives a unique token mapped to their email.

3. **Voting**  
   - A voter visits `/votar?token=...`.  
   - The form displays the voting entity, logo, and available options.  
   - Submitting a vote updates the encrypted file and records the action in logs.

4. **Audit**  
   - Accessed via `/admin_audit?voting_id={...}&key={...}`.  
   - Displays all actions with timestamps.

5. **Encryption & Security**  
   - Files are encrypted so only those with the correct key can read or modify them.  
   - Tokens ensure each voter can only cast a single vote.

## To-do items for upcoming functions

- [ ] Close (manually) a vote, it will be marked as finished
- [ ] Mark the voting end date (automatically)
- [ ] ...

## Prerequisites

To get the most out of this guide, you’ll need to:

* Install `virtualenv` by running `pip install virtualenv`

## Running the project locally

1. Create the Python virtual environment

```sh
python3 -m venv vote-online
```

```sh
source vote-online/bin/activate
```

2. Install dependencies:

It is recommended, first, upgrade pip:
```sh
pip install --upgrade pip
```

Install dependencies/requirements:
```sh
pip install -r requirements.txt
```

3. (Optional) Have in your Local the `.env` file created with the credentials, you can use the `.env.example` file as a template.

4. Execute the following command:

```sh
uvicorn app.main:app --reload --port 3000 --host 0.0.0.0
```

Or if you want to see the logs:

```sh
uvicorn main:app --reload --port 3000 --host 0.0.0.0 --log-level debug
```

Or in background:

```sh
nohup uvicorn main:app --reload --port 8888 --host 0.0.0.0 &
```

5. You should see an output similar to:

```
INFO:     Uvicorn running on http://127.0.0.1:3000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Licensing

All packages in this repository are open-source software and licensed under the [MIT License](https://github.com/joakimvivas/marco-bot/blob/main/LICENSE). By contributing in this repository, you agree to release your code under this license as well.

Let's build the future of the **Electronic Voting System** together!